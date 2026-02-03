from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import transaction
from django.db.models import F
from django.http import HttpResponseForbidden, JsonResponse
from django.shortcuts import render, get_object_or_404
from django.views import View
from django.views.decorators.http import require_POST
from django.views.generic import ListView
import json

from apps.dictionary.models import Word
from apps.lists.models import SubtitleList
from apps.study.models import KnownWord


@login_required
@require_POST
def toggle_known_word(request):
    word_id = request.POST.get("word_id")
    if not word_id:
        return JsonResponse(
            {"status": "error", "message": "word_id required"}, status=400
        )

    try:
        word = Word.objects.get(id=word_id)
    except Word.DoesNotExist:
        return JsonResponse(
            {"status": "error", "message": "Word not found"}, status=404
        )

    known_obj, created = KnownWord.objects.get_or_create(user=request.user, word=word)

    if not created:
        # уже было — удаляем
        known_obj.delete()
        return JsonResponse({"status": "ok", "known": False})

    return JsonResponse({"status": "ok", "known": True})


def word_mini_cards(request, list_id):
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
            KnownWord.objects.filter(
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
        return KnownWord.objects.filter(user=self.request.user).select_related("word")


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

        known_qs = KnownWord.objects.filter(user=request.user, word=word)

        if known_qs.exists():
            # ❌ убираем "выученное"
            known_qs.delete()

            SubtitleList.objects.filter(id=word_list.id).update(
                quantity_learned_words=F("quantity_learned_words") - 1
            )

            known_state = False
        else:
            # ✅ добавляем "выученное"
            KnownWord.objects.create(user=request.user, word=word)

            SubtitleList.objects.filter(id=word_list.id).update(
                quantity_learned_words=F("quantity_learned_words") + 1
            )

            known_state = True

        # получаем актуальное значение (уже обновлённое)
        word_list.refresh_from_db(fields=["quantity_learned_words"])

        return JsonResponse(
            {
                "status": "ok",
                "known": known_state,
                "quantity_learned_words": word_list.quantity_learned_words,
            }
        )


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
