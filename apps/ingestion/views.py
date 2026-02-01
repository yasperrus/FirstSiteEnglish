from better_profanity import profanity
from django.contrib.auth.mixins import LoginRequiredMixin

from django.http import JsonResponse
from django.urls import reverse
from django.views import View

from apps.dictionary.models import Word
from apps.ingestion.services.subtitle_parser_nltk_fast import ConvertTextToSubtitleWords
from apps.lists.models import SubtitleList, UserSubtitleList, SubtitleListWord


class SaveSubtitleListView(LoginRequiredMixin, View):
    MAX_IMAGE_SIZE = 2 * 1024 * 1024
    ALLOWED_CONTENT_TYPES = ["image/jpeg", "image/png", "image/webp"]

    def post(self, request):
        data = request.POST
        subtitle_name = data.get("subtitle_name")
        background_color = request.POST.get("background_color", "#ffffff")
        background_image = request.FILES.get("background_image")

        if background_image:
            if background_image.content_type not in self.ALLOWED_CONTENT_TYPES:
                return JsonResponse(
                    {
                        "status": "error",
                        "message": "Недопустимый формат файла. Разрешены: jpg, png, webp.",
                    },
                    status=400,
                )

            if background_image and background_image.size > self.MAX_IMAGE_SIZE:
                return JsonResponse(
                    {
                        "status": "error",
                        "message": "Файл слишком большой. Максимальный размер — 2 МБ.",
                    },
                    status=400,
                )

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
            background_color=background_color,
            background_image=background_image,
            quantity_words=len(words_data),
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
                continue

        return JsonResponse({"status": "ok", "redirect_url": reverse("lists:my_lists")})


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

        return JsonResponse({"subtitle_name": subtitle_name, "words": words_list})
