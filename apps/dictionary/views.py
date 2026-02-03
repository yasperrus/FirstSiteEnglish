from django.db.models import Exists, OuterRef, Case, When, Value, IntegerField
from django.http import JsonResponse
from django.shortcuts import render
from django.db.models import Prefetch
from django.core.paginator import Paginator

from apps.dictionary.models import Word, PartOfSpeech

PAGE_SIZE = 100


def dictionary_view(request):
    return render(request, "dictionary/dictionary.html")


def dictionary_api(request):
    page = int(request.GET.get("page", 1))
    q = request.GET.get("q", "").strip()

    qs = (
        Word.objects.all()
        .prefetch_related(
            Prefetch(
                "parts_of_speech",
                queryset=PartOfSpeech.objects.prefetch_related("translations"),
            )
        )
        .order_by("name")
    )

    if q:
        qs = (
            qs.filter(name__icontains=q)
            .annotate(
                relevance=Case(
                    # 1️⃣ точное совпадение
                    When(name__iexact=q, then=Value(0)),
                    # 2️⃣ начинается с запроса
                    When(name__istartswith=q, then=Value(1)),
                    # 3️⃣ содержит внутри
                    When(name__icontains=q, then=Value(2)),
                    default=Value(3),
                    output_field=IntegerField(),
                )
            )
            .order_by("relevance", "name")
        )

    paginator = Paginator(qs, PAGE_SIZE)
    page_obj = paginator.get_page(page)

    results = []
    for word in page_obj:
        results.append(
            {
                "id": word.id,
                "name": word.name,
                "transcription": word.transcription,
                "parts_of_speech": [
                    {
                        "name": pos.name,
                        "translations": [t.translation for t in pos.translations.all()],
                    }
                    for pos in word.parts_of_speech.all()
                ],
            }
        )

    return JsonResponse(
        {
            "results": results,
            "has_next": page_obj.has_next(),
        }
    )
