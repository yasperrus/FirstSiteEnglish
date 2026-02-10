from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import F
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import ListView
import json

from apps.dictionary.models import Word
from apps.lists.models import SubtitleList
from apps.study.models import UserWordProgress
from apps.study.services.word_selection import (
    get_words_for_test,
    ensure_user_list_progress,
    get_words_json_for_test,
)

from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render
from django.db.models import Prefetch


@login_required
def word_mini_cards(request, list_id):
    word_list = get_object_or_404(SubtitleList, id=list_id)

    words = word_list.words.all()

    progress_qs = UserWordProgress.objects.filter(
        user=request.user,
        word__in=words,
    )

    progress_map = {p.word_id: p for p in progress_qs}

    return render(
        request,
        "study/word_mini_cards.html",
        {
            "word_list": word_list,
            "words": words,
            "progress_map": progress_map,
        },
    )


from django.views import View
from django.http import JsonResponse
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.decorators.http import require_POST
from django.utils.decorators import method_decorator
from django.shortcuts import get_object_or_404
from django.db import transaction


@method_decorator(require_POST, name="dispatch")
class UpdateWordStateView(LoginRequiredMixin, View):

    def post(self, request, *args, **kwargs):
        word_id = request.POST.get("word_id")
        mode = request.POST.get("mode")  # learning | learned

        if not word_id or mode not in ("learning", "learned"):
            return JsonResponse(
                {"status": "error", "message": "invalid params"},
                status=400,
            )

        word = get_object_or_404(Word, id=word_id)

        with transaction.atomic():
            progress, _ = UserWordProgress.objects.get_or_create(
                user=request.user,
                word=word,
            )

            if mode == "learning":
                progress.is_learning = not progress.is_learning
                if progress.is_learning:
                    progress.is_learned = False

            elif mode == "learned":
                progress.is_learned = not progress.is_learned
                if progress.is_learned:
                    progress.is_learning = False

            progress.save(update_fields=["is_learning", "is_learned"])

        return JsonResponse(
            {
                "status": "ok",
                "state": {
                    "is_learning": progress.is_learning,
                    "is_learned": progress.is_learned,
                },
            }
        )


def word_mini_cards_(request, list_id):
    word_list = get_object_or_404(SubtitleList, id=list_id)

    if not word_list.is_public:
        if not request.user.is_authenticated:
            return HttpResponseForbidden()
        if request.user != word_list.owner and not request.user.is_staff:
            return HttpResponseForbidden()

    words = word_list.words.all()

    known_word_ids = set()
    if request.user.is_authenticated:
        known_word_ids = set(
            UserWordProgress.objects.filter(
                user=request.user, word__subtitle_lists=word_list
            ).values_list("word_id", flat=True)
        )

    return render(
        request,
        "study/word_mini_cards.html",
        {
            "word_list": word_list,
            "words": words,
            "known_word_ids": known_word_ids,
        },
    )


class KnownWordsView(LoginRequiredMixin, ListView):
    template_name = "study/known_word_mini_cards.html"
    context_object_name = "known_words"
    paginate_by = 30

    def get_queryset(self):
        return UserWordProgress.objects.filter(
            user=self.request.user, is_learned=True
        ).select_related("word")


class ToggleKnownWordView(LoginRequiredMixin, View):
    @transaction.atomic
    def post(self, request):
        word_id = request.POST.get("word_id")
        list_id = request.POST.get("list_id")

        if not word_id or not list_id:
            return JsonResponse({"status": "error"}, status=400)

        try:
            word_list = SubtitleList.objects.select_for_update().get(id=list_id)
            word = Word.objects.get(id=word_id)
        except (SubtitleList.DoesNotExist, Word.DoesNotExist):
            return JsonResponse({"status": "error"}, status=404)

        # ⚠️ защита: слово должно реально принадлежать списку
        if not word_list.words.filter(id=word.id).exists():
            return JsonResponse({"status": "error"}, status=403)

        known_qs = UserWordProgress.objects.filter(user=request.user, word=word)

        if known_qs.exists():
            # ❌ убираем "выученное"
            known_qs.delete()

            known_state = False
        else:
            # ✅ добавляем "выученное"
            UserWordProgress.objects.create(user=request.user, word=word)

        return JsonResponse(
            {
                "status": "ok",
            }
        )


@login_required
def study_words_view(request, list_id):
    """
    Страница изучения слов.
    JS ожидает words_json в старом формате — мы его сохраняем.
    """

    subtitle_list = get_object_or_404(
        SubtitleList,
        id=list_id,
        is_hide=False,
    )

    # 1️⃣ Гарантируем прогресс и слова
    ensure_user_list_progress(
        user=request.user,
        subtitle_list=subtitle_list,
    )

    # 2️⃣ Получаем слова под JS
    words_json = get_words_json_for_test(
        user=request.user,
        subtitle_list=subtitle_list,
        limit=20,
    )

    return render(
        request,
        "study/study.html",
        {
            "subtitle_list": subtitle_list,
            "words_json": words_json,
        },
    )


@login_required
def study_easy_3_words_view(request, list_id):
    """
    Страница изучения слов.
    JS ожидает words_json в старом формате — мы его сохраняем.
    """

    subtitle_list = get_object_or_404(
        SubtitleList,
        id=list_id,
        is_hide=False,
    )

    # 1️⃣ Гарантируем прогресс и слова
    ensure_user_list_progress(
        user=request.user,
        subtitle_list=subtitle_list,
    )

    # 2️⃣ Получаем слова под JS
    words_json = get_words_json_for_test(
        user=request.user,
        subtitle_list=subtitle_list,
        limit=20,
        with_all_translations=False,
        with_distractors=True,
    )

    return render(
        request,
        "study/study_easy_3.html",
        {
            "subtitle_list": subtitle_list,
            "words_json": words_json,
        },
    )


@login_required
def study_puzzle_words_view(request, list_id):
    """
    Страница изучения слов.
    JS ожидает words_json в старом формате — мы его сохраняем.
    """

    subtitle_list = get_object_or_404(
        SubtitleList,
        id=list_id,
        is_hide=False,
    )

    # 1️⃣ Гарантируем прогресс и слова
    ensure_user_list_progress(
        user=request.user,
        subtitle_list=subtitle_list,
    )

    # 2️⃣ Получаем слова под JS
    words_json = get_words_json_for_test(
        user=request.user,
        subtitle_list=subtitle_list,
        limit=20,
        with_all_translations=False,
        with_distractors=False,
    )

    return render(
        request,
        "study/study_puzzle_2.html",
        {
            "subtitle_list": subtitle_list,
            "words_json": words_json,
        },
    )


@login_required
def study_easy_words_view(request, list_id):
    """
    Страница изучения слов.
    JS ожидает words_json в старом формате — мы его сохраняем.
    """

    subtitle_list = get_object_or_404(
        SubtitleList,
        id=list_id,
        is_hide=False,
    )

    # 1️⃣ Гарантируем прогресс и слова
    ensure_user_list_progress(
        user=request.user,
        subtitle_list=subtitle_list,
    )

    # 2️⃣ Получаем слова под JS
    words_json = get_words_json_for_test(
        user=request.user,
        subtitle_list=subtitle_list,
        limit=20,
        with_all_translations=False,
        with_distractors=True,
    )

    return render(
        request,
        "study/study_easy.html",
        {
            "subtitle_list": subtitle_list,
            "words_json": words_json,
        },
    )


@login_required
def study_easy_2_words_view(request, list_id):
    subtitle_list = get_object_or_404(
        SubtitleList,
        id=list_id,
        is_hide=False,
    )

    # 1️⃣ Гарантируем прогресс и слова
    ensure_user_list_progress(
        user=request.user,
        subtitle_list=subtitle_list,
    )

    # 2️⃣ Получаем слова под JS
    words_json = get_words_json_for_test(
        user=request.user,
        subtitle_list=subtitle_list,
        limit=20,
    )

    return render(
        request,
        "study/study_easy_2.html",
        {
            "subtitle_list": subtitle_list,
            "words_json": words_json,
        },
    )


@login_required
@require_POST
def submit_answer(request):
    """
    Получает результат одного клика по варианту ответа.
    НЕ сохраняет варианты ответов.
    """

    try:
        data = json.loads(request.body)
    except json.JSONDecodeError:
        return JsonResponse({"error": "Invalid JSON"}, status=400)

    word_name = data.get("word")
    is_correct = data.get("is_correct")

    if word_name is None or is_correct is None:
        return JsonResponse({"error": "Missing data"}, status=400)

    word = get_object_or_404(Word, name=word_name)

    progress = get_object_or_404(
        UserWordProgress,
        user=request.user,
        word=word,
    )

    # 🔄 обновляем дату просмотра всегда
    progress.last_reviewed_at = timezone.now()

    # 🎯 логика score
    if is_correct:
        if progress.score < 4:
            progress.score += 1
    else:
        progress.score = max(0, progress.score - 1)

    progress.save(
        update_fields=[
            "score",
            "last_reviewed_at",
            "updated_at",
        ]
    )

    return JsonResponse({"ok": True, "score": progress.score})


def study_cards(request, list_id):
    subtitle_list = get_object_or_404(
        SubtitleList.objects.prefetch_related("words__parts_of_speech__translations"),
        id=list_id,
    )

    words = []

    for w in subtitle_list.words.all():

        # ВСЕ переводы (для проверки)
        all_translations = []

        for pos in w.parts_of_speech.all():
            all_translations.extend(
                pos.translations.values_list("translation", flat=True)
            )

        all_translations = list(set(t.strip().lower() for t in all_translations if t))

        # ОСНОВНОЙ перевод (для показа)
        main_translation = ""

        main_pos = w.parts_of_speech.filter(is_main=True).first()
        if main_pos:
            main_tr = main_pos.translations.filter(is_main=True).first()
            if main_tr:
                main_translation = main_tr.translation
            else:
                first_tr = main_pos.translations.first()
                if first_tr:
                    main_translation = first_tr.translation

        words.append(
            {
                "word": w.name,
                "transcription": w.transcription,
                "main_translation": main_translation,
                "all_translations": all_translations,
            }
        )

    return render(
        request,
        "study/study.html",
        {
            "subtitle_list": subtitle_list,
            "words_json": json.dumps(words, ensure_ascii=False),
        },
    )
