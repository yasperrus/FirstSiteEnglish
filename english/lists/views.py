# lists/views.py
import json

from better_profanity import profanity
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db import models
from django.shortcuts import render, get_object_or_404, redirect
from django.http import JsonResponse, HttpResponseForbidden
from django.urls import reverse
from django.views import View
from django.views.decorators.http import require_POST

from lists.models import (
    SubtitleList,
    PathOfSpeech,
    Translation,
    Word,
    SubtitleListWord,
    UserSubtitleList,
    SubtitleListLike,
)
from lists.services.subtitle_parser_nltk_fast import ConvertTextToSubtitleWords

def about(request):
    return render(request, "lists/about.html")

def word_list_edit():
    return ''

from django.db.models import Exists, OuterRef

def public_lists(request):
    qs = SubtitleList.objects.filter(
        is_public=True,
        is_hide=False,
    ).select_related("owner").prefetch_related("likes")

    if request.user.is_authenticated:
        qs = qs.annotate(
            is_liked=Exists(
                SubtitleListLike.objects.filter(
                    subtitle_list=OuterRef("pk"),
                    user=request.user
                )
            )
        )
    else:
        qs = qs.annotate(
            is_liked=models.Value(False, output_field=models.BooleanField())
        )

    qs = qs.order_by("-modified_time")

    return render(request, "lists/word_lists.html", {
        "word_lists": qs,
        "is_public_page": True,
    })


@login_required
@require_POST
def delete_list(request, list_id):
    subtitle_list = get_object_or_404(SubtitleList, id=list_id)

    # 🔐 проверка владельца
    if not subtitle_list.users.filter(id=request.user.id).exists():
        return JsonResponse({"error": "forbidden"}, status=403)

    subtitle_list.delete()
    return JsonResponse({"status": "ok"})

@login_required
@require_POST
def toggle_publish(request, pk):
    subtitle_list = get_object_or_404(SubtitleList, pk=pk)

    # ПРАВА ДОСТУПА
    if subtitle_list.owner != request.user and not request.user.is_staff:
        return HttpResponseForbidden()

    subtitle_list.is_public = not subtitle_list.is_public
    subtitle_list.save(update_fields=["is_public"])

    return JsonResponse({
        "is_public": subtitle_list.is_public
    })

@login_required
@require_POST
def toggle_like(request, pk):
    subtitle_list = get_object_or_404(
        SubtitleList,
        pk=pk,
        is_public=True
    )

    like, created = SubtitleListLike.objects.get_or_create(
        user=request.user,
        subtitle_list=subtitle_list
    )

    if not created:
        like.delete()
        liked = False
    else:
        liked = True

    return JsonResponse({
        "liked": liked,
        "likes_count": subtitle_list.likes.count()
    })


def my_lists(request):
    qs = SubtitleList.objects.filter(owner=request.user)

    if request.user.is_authenticated:
        qs = qs.annotate(
            is_liked=Exists(
                SubtitleListLike.objects.filter(
                    subtitle_list=OuterRef("pk"),
                    user=request.user
                )
            )
        )

    return render(request, "lists/word_lists.html", {
        "word_lists": qs,
        "is_my_lists": True,
    })

@login_required
def word_lists(request):
    lists = (
        SubtitleList.objects
        .filter(users=request.user)
        .order_by("-modified_time")
    )

    return render(request, "lists/word_lists.html", {
        "word_lists": lists
    })

def word_list_detail(request, list_id):
    word_list = get_object_or_404(
        SubtitleList.objects.prefetch_related(
            'words__parts_of_speech__translations'
        ),
        id=list_id
    )

    if not word_list.is_public:
        if not request.user.is_authenticated:
            return HttpResponseForbidden()

        if request.user != word_list.owner and not request.user.is_staff:
            return HttpResponseForbidden()

    return render(request, "lists/word_list_detail.html", {
        "word_list": word_list
    })


def get_translations(request, word_id):
    part_id = request.GET.get('part')
    translations = Translation.objects.filter(path_of_speech_id=part_id).values(
        'id', 'translation', 'is_main'
    )
    data = list(translations)
    # Переименуем ключ 'translation' в 'value' для JS
    for t in data:
        t['value'] = t.pop('translation')
    return JsonResponse(data, safe=False)


class SubtitlePreviewView(LoginRequiredMixin, View):
    def post(self, request):
        file = request.FILES.get("subtitle_file")
        text = request.POST.get("subtitle_text", "").strip()

        source_text = None
        subtitle_name = None

        if file:
            try:
                source_text = file.read().decode("utf-8")
                subtitle_name = file.name
            except UnicodeDecodeError:
                return JsonResponse(
                    {"error": "Не удалось прочитать файл. Используйте UTF-8"},
                    status=400,
                )
        elif text:
            source_text = text

        else:
            return JsonResponse({"error": "Не передан ни файл, ни текст"}, status=400)

        if not source_text.strip():
            return JsonResponse({"error": "Пустой текст для обработки"}, status=400)

        try:
            parser = ConvertTextToSubtitleWords(source_text)
            words_list = parser.to_dict()
        except Exception as e:
            return JsonResponse({"error": f"Ошибка обработки: {str(e)}"}, status=500)

        return JsonResponse({
            "subtitle_name": subtitle_name,
            "words": words_list
        })


class SaveSubtitleListView(LoginRequiredMixin, View):
    def post(self, request):
        data = request.POST
        subtitle_name = data.get("subtitle_name")

        if profanity.contains_profanity(subtitle_name):
            return JsonResponse(
                {
                    "status": "error",
                    "message": "В названии списка недопустима ненормативная лексика",
                },
                status=400,
            )

        words_data = request.POST.getlist("words")

        subtitle_list = SubtitleList.objects.create(
            name=subtitle_name,
            owner=request.user,
        )

        UserSubtitleList.objects.create(user=request.user, subtitle_list=subtitle_list)

        import json

        for w_str in words_data:
            try:
                w = json.loads(w_str)
                word = Word.objects.get(name=w["name"])
                SubtitleListWord.objects.create(
                    subtitle_list=subtitle_list, word=word, frequency=w["frequency"]
                )
            except (json.JSONDecodeError, Word.DoesNotExist, KeyError):
                continue  # пропускаем битые записи

        return JsonResponse({"status": "ok", "redirect_url": reverse("my_lists")})

def study_cards(request, list_id):
    subtitle_list = get_object_or_404(
        SubtitleList.objects.prefetch_related(
            "words__parts_of_speech__translations"
        ),
        id=list_id
    )

    words = []

    for w in subtitle_list.words.all():

        # ВСЕ переводы (для проверки)
        all_translations = []

        for pos in w.parts_of_speech.all():
            all_translations.extend(
                pos.translations.values_list("translation", flat=True)
            )

        all_translations = list(
            set(t.strip().lower() for t in all_translations if t)
        )

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

        words.append({
            "word": w.name,
            "transcription": w.transcription,
            "main_translation": main_translation,
            "all_translations": all_translations,
        })

    return render(request, "lists/study.html", {
        "subtitle_list": subtitle_list,
        "words_json": json.dumps(words, ensure_ascii=False),
    })
