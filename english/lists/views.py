# lists/views.py
import json

from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render, get_object_or_404
from django.http import JsonResponse
from django.views import View
from django.views.decorators.http import require_POST

from lists.models import (
    SubtitleList,
    PathOfSpeech,
    Translation,
    Word,
    SubtitleListWord,
    UserSubtitleList,
)
from lists.services.subtitle_parser import ConvertTextToSubtitleWords

def about(request):
    return render(request, "lists/about.html")

def word_list_edit():
    return ''

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
        if not file:
            return JsonResponse({"error": "Файл не загружен"}, status=400)

        try:
            text = file.read().decode("utf-8")
        except UnicodeDecodeError:
            return JsonResponse({"error": "Не удалось прочитать файл. Используйте UTF-8"}, status=400)


        parser = ConvertTextToSubtitleWords(text)
        words_list = parser.to_dict()

        return JsonResponse({
            "subtitle_name": file.name,
            "words": words_list
        })


class SaveSubtitleListView(LoginRequiredMixin, View):
    def post(self, request):
        data = request.POST
        subtitle_name = data.get("subtitle_name")
        words_data = request.POST.getlist("words")

        subtitle_list = SubtitleList.objects.create(
            name=subtitle_name
        )

        UserSubtitleList.objects.create(user=request.user, subtitle_list=subtitle_list)

        import json
        for w_str in words_data:
            w = json.loads(w_str)
            try:
                word = Word.objects.get(name=w["name"])
            except Word.DoesNotExist:
                continue
            SubtitleListWord.objects.create(
                subtitle_list=subtitle_list,
                word=word,
                frequency=w["frequency"]
            )
        return JsonResponse({"status": "ok"})

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

