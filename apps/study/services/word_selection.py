import json
import random
from datetime import datetime

from django.db import transaction
from django.db.models import Case, When, Value, IntegerField
from django.db.models.functions import Coalesce, Random
from django.utils import timezone

from apps.dictionary.models import Word
from apps.lists.models import UserSubtitleListProgress, SubtitleListWord
from apps.study.models import UserWordProgress


@transaction.atomic
def ensure_user_list_progress(user, subtitle_list):
    """
    Гарантирует, что:
    - существует UserSubtitleListProgress с актуальной версией
    - все слова списка присутствуют в UserWordProgress
    """

    progress = UserSubtitleListProgress.objects.filter(
        user=user,
        subtitle_list=subtitle_list,
    ).first()

    if progress and progress.version == subtitle_list.version:
        return  # всё уже актуально

    # Все word_id из списка
    list_word_ids = SubtitleListWord.objects.filter(
        subtitle_list=subtitle_list
    ).values_list("word_id", flat=True)

    # Уже существующие у пользователя
    existing_word_ids = set(
        UserWordProgress.objects.filter(
            user=user,
            word_id__in=list_word_ids,
        ).values_list("word_id", flat=True)
    )

    # Недостающие
    to_create = [
        UserWordProgress(
            user=user,
            word_id=word_id,
        )
        for word_id in list_word_ids
        if word_id not in existing_word_ids
    ]

    if to_create:
        UserWordProgress.objects.bulk_create(
            to_create,
            ignore_conflicts=True,
        )

    # Обновляем / создаём прогресс списка
    UserSubtitleListProgress.objects.update_or_create(
        user=user,
        subtitle_list=subtitle_list,
        defaults={
            "version": subtitle_list.version,
        },
    )


# def get_words_json_for_test_(user, subtitle_list, limit=20):
#     """
#     Возвращает JSON со словами в формате,
#     который ожидает старый JS
#     """
#
#     progress_qs = get_words_for_test(
#         user=user,
#         subtitle_list=subtitle_list,
#         limit=limit,
#     )
#
#     words = []
#
#     for p in progress_qs:
#         w = p.word
#
#         # --- все переводы (для проверки) ---
#         all_translations = set()
#
#         for pos in w.parts_of_speech.all():
#             for tr in pos.translations.all():
#                 if tr.translation:
#                     all_translations.add(tr.translation.strip().lower())
#
#         # --- основной перевод (для показа) ---
#         main_translation = ""
#
#         main_pos = w.parts_of_speech.filter(is_main=True).first()
#         if main_pos:
#             main_tr = main_pos.translations.filter(is_main=True).first()
#             if main_tr:
#                 main_translation = main_tr.translation
#             else:
#                 first_tr = main_pos.translations.first()
#                 if first_tr:
#                     main_translation = first_tr.translation
#
#         words.append(
#             {
#                 "word": w.name,
#                 "transcription": w.transcription,
#                 "main_translation": main_translation,
#                 "all_translations": list(all_translations),
#             }
#         )
#
#     return json.dumps(words, ensure_ascii=False)


def get_words_for_test(user, subtitle_list, limit=20):
    """
    Возвращает queryset UserWordProgress,
    отсортированный по приоритету изучения
    """

    return (
        UserWordProgress.objects.filter(
            user=user,
            word__subtitle_lists=subtitle_list,
            is_hidden=False,
        )
        .select_related("word")
        .prefetch_related("word__parts_of_speech__translations")
        .annotate(
            learned_weight=Case(
                When(is_learned=True, then=Value(1)),
                default=Value(0),
                output_field=IntegerField(),
            ),
            review_weight=Coalesce(
                "last_reviewed_at",
                timezone.make_aware(datetime.min),
            ),
        )
        .order_by(
            "learned_weight",
            "score",
            "level_learned",
            "review_weight",
            Random(),
        )[:limit]
    )


def get_words_data_for_test(user, subtitle_list, limit=20, with_all_translations=False):
    progress_qs = get_words_for_test(user, subtitle_list, limit)
    words = []

    for p in progress_qs:
        w = p.word
        main_pos = w.parts_of_speech.filter(is_main=True).first()
        main_translation = get_main_translation(main_pos)

        word_dict = {
            "pk": w.pk,
            "word": w.name,
            "transcription": w.transcription,
            "main_translation": main_translation,
        }

        if with_all_translations:
            all_translations = set()
            for pos in w.parts_of_speech.all():
                for tr in pos.translations.all():
                    if tr.translation:
                        all_translations.add(tr.translation.strip())
            word_dict["all_translations"] = list(all_translations)

        words.append(word_dict)

    return words


def get_words_json_for_test(
    user, subtitle_list, limit=20, with_distractors=False, with_all_translations=False
):
    words = get_words_data_for_test(
        user, subtitle_list, limit, with_all_translations=with_all_translations
    )

    if with_distractors:
        for word_obj in words:
            # word_obj — это словарь
            word_instance = Word.objects.get(name=word_obj["word"])
            word_obj["distractors"] = get_distractors(
                word_instance, word_obj["main_translation"], limit=3
            )

    return json.dumps(words, ensure_ascii=False)


def get_distractors(word_instance, correct_translation, limit=3):
    """
    word_instance — объект Word
    correct_translation — строка перевода, который нужно исключить
    """
    main_pos = word_instance.parts_of_speech.filter(is_main=True).first()
    if not main_pos:
        return []

    pos_name = main_pos.name

    candidate_ids = list(
        Word.objects.filter(parts_of_speech__name=pos_name)
        .exclude(id=word_instance.id)
        .values_list("id", flat=True)
    )

    if not candidate_ids:
        return []

    import random

    chosen_ids = random.sample(candidate_ids, min(limit, len(candidate_ids)))

    distractors = []
    words = Word.objects.filter(id__in=chosen_ids).prefetch_related(
        "parts_of_speech__translations"
    )
    for w in words:
        mp = w.parts_of_speech.filter(is_main=True).first()
        tr = get_main_translation(mp)
        if tr and tr != correct_translation:
            distractors.append(tr)

    return distractors[:limit]


def get_main_translation(pos):
    """Возвращает перевод части речи. Сначала ищет is_main=True, иначе первый."""
    main_tr = pos.translations.filter(is_main=True).first()
    if main_tr:
        return main_tr.translation
    first_tr = pos.translations.first()
    return first_tr.translation if first_tr else ""
