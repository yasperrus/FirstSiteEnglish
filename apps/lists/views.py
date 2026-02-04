import json

from django.db.models import Exists, OuterRef, Case, When, Value, IntegerField, Prefetch
from django.contrib.auth.decorators import login_required
from django.db import models
from django.db.models.signals import pre_save, post_delete
from django.dispatch import receiver
from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
from django.shortcuts import get_object_or_404, render
from django.http import HttpResponseForbidden

from apps.lists.models import SubtitleList, UserSubtitleList

from django.http import JsonResponse

from ..dictionary.models import Word, PartOfSpeech, Translation
from ..social.models import SubtitleListLike
from ..study.models import UserWordProgress

from tabulate import tabulate


@login_required
def download_words(request, list_id):
    ids = request.GET.get("ids", "")
    ids = [int(i) for i in ids.split(",") if i.isdigit()]

    subtitle_list = get_object_or_404(SubtitleList, id=list_id)

    words = Word.objects.filter(
        id__in=ids, subtitle_lists=subtitle_list
    ).prefetch_related("parts_of_speech__translations")

    table = []

    for w in words:
        translation = ""

        main_pos = w.parts_of_speech.filter(is_main=True).first()
        if not main_pos:
            main_pos = w.parts_of_speech.first()

        if main_pos:
            main_tr = main_pos.translations.filter(is_main=True).first()
            if main_tr:
                translation = main_tr.translation
            else:
                first_tr = main_pos.translations.first()
                if first_tr:
                    translation = first_tr.translation

        table.append([w.name, w.transcription, translation])

    content = tabulate(
        table, headers=["WORD", "TRANSCRIPTION", "TRANSLATION"], tablefmt="plain"
    )

    filename = f"{subtitle_list.name}.words.txt"

    response = HttpResponse(content, content_type="text/plain; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response


def about(request):
    return render(request, "lists/about.html")


def word_list_edit(request, list_id):
    return ""


def public_lists(request):
    qs = (
        SubtitleList.objects.filter(
            is_public=True,
            is_hide=False,
        )
        .select_related("owner")
        .prefetch_related("likes")
        .order_by("-modified_time")
    )

    if request.user.is_authenticated:
        qs = qs.annotate(
            is_liked=Exists(
                SubtitleListLike.objects.filter(
                    subtitle_list=OuterRef("pk"), user=request.user
                )
            )
        )
        # Получаем состояния пользователя
        user_states = UserSubtitleList.objects.filter(user=request.user)
        user_state_dict = {us.subtitle_list_id: us for us in user_states}

        # Присваиваем is_open_menu без лишнего запроса
        for lst in qs:
            user_state = user_state_dict.get(lst.id)
            lst.is_open_menu = user_state.is_open_menu if user_state else False

    else:
        qs = qs.annotate(
            is_liked=models.Value(False, output_field=models.BooleanField())
        )
        for lst in qs:
            lst.is_open_menu = False

    # qs = qs

    return render(
        request,
        "lists/lists.html",
        {
            "word_lists": qs,
            "is_public_page": True,
        },
    )


def my_lists(request):
    qs = (
        SubtitleList.objects.filter(owner=request.user)
        .select_related("owner")
        .order_by("-modified_time")
    )

    if request.user.is_authenticated:
        qs = qs.annotate(
            is_liked=Exists(
                SubtitleListLike.objects.filter(
                    subtitle_list=OuterRef("pk"), user=request.user
                )
            )
        )
        user_states = UserSubtitleList.objects.filter(user=request.user)
        qs = qs.prefetch_related(Prefetch("usersubtitlelist_set", queryset=user_states))
        for lst in qs:
            user_state = lst.usersubtitlelist_set.first()
            lst.is_open_menu = user_state.is_open_menu if user_state else False

    return render(
        request,
        "lists/lists.html",
        {
            "word_lists": qs,
            "is_my_lists": True,
        },
    )


@login_required
@require_POST
def delete_list(request, list_id):
    subtitle_list = get_object_or_404(SubtitleList, id=list_id)

    # 🔐 проверка владельца
    if not subtitle_list.users.filter(id=request.user.id).exists():
        return JsonResponse({"error": "forbidden"}, status=403)

    subtitle_list.delete()
    return JsonResponse({"status": "ok"})


@receiver(post_delete, sender=SubtitleList)
def delete_background_image(sender, instance, **kwargs):
    if instance.background_image:
        instance.background_image.delete(save=False)


@receiver(pre_save, sender=SubtitleList)
def delete_old_image_on_change(sender, instance, **kwargs):
    if not instance.pk:
        return

    try:
        old = SubtitleList.objects.get(pk=instance.pk)
    except SubtitleList.DoesNotExist:
        return

    if old.background_image and old.background_image != instance.background_image:
        old.background_image.delete(save=False)


@csrf_exempt
def toggle_menu(request, list_id):
    if request.method == "POST" and request.user.is_authenticated:
        try:
            data = json.loads(request.body)
            is_open = data.get("is_open_menu", False)

            lst = SubtitleList.objects.get(pk=list_id)

            # Получаем или создаем запись для текущего пользователя
            user_state, _ = UserSubtitleList.objects.get_or_create(
                user=request.user, subtitle_list=lst
            )
            print("Saving is_open_menu:", is_open)
            user_state.is_open_menu = is_open
            user_state.save()
            print("Saved:", user_state.is_open_menu)

            return JsonResponse({"success": True, "is_open_menu": is_open})
        except SubtitleList.DoesNotExist:
            return JsonResponse({"success": False, "error": "Not found"}, status=404)

    return JsonResponse({"success": False}, status=400)


@login_required
@require_POST
def toggle_publish(request, pk):
    subtitle_list = get_object_or_404(SubtitleList, pk=pk)

    # ПРАВА ДОСТУПА
    if subtitle_list.owner != request.user and not request.user.is_staff:
        return HttpResponseForbidden()

    subtitle_list.is_public = not subtitle_list.is_public
    subtitle_list.save(update_fields=["is_public"])

    return JsonResponse({"is_public": subtitle_list.is_public})


@login_required
def word_lists(request):
    lists = SubtitleList.objects.filter(users=request.user).order_by("-modified_time")

    return render(request, "lists/word_lists.html", {"word_lists": lists})


def word_list_detail(request, list_id):
    word_list = get_object_or_404(SubtitleList, id=list_id)

    if not word_list.is_public:
        if not request.user.is_authenticated:
            return HttpResponseForbidden()
        if request.user != word_list.owner and not request.user.is_staff:
            return HttpResponseForbidden()

    words = (
        word_list.words.all()
        .annotate(
            is_known=Exists(
                UserWordProgress.objects.filter(user=request.user, word=OuterRef("pk"))
            )
        )
        .prefetch_related("parts_of_speech__translations")
    )

    return render(
        request,
        "lists/word_list_detail.html",
        {
            "word_list": word_list,
            "words": words,
        },
    )


# def word_list_detail(request, list_id):
#     word_list = get_object_or_404(
#         SubtitleList.objects.prefetch_related(
#             'words__parts_of_speech__translations'
#         ),
#         id=list_id
#     )
#
#     if not word_list.is_public:
#         if not request.user.is_authenticated:
#             return HttpResponseForbidden()
#
#         if request.user != word_list.owner and not request.user.is_staff:
#             return HttpResponseForbidden()
#
#     return render(request, "lists/word_list_detail.html", {
#         "word_list": word_list
#     })


def get_translations(request, word_id):
    part_id = request.GET.get("part")
    translations = Translation.objects.filter(path_of_speech_id=part_id).values(
        "id", "translation", "is_main"
    )
    data = list(translations)
    # Переименуем ключ 'translation' в 'value' для JS
    for t in data:
        t["value"] = t.pop("translation")
    return JsonResponse(data, safe=False)
