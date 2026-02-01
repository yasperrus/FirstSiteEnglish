from django.conf import settings
from django.db import models


def subtitle_list_image_path(instance, filename):
    return f"images/lists/{instance.owner.username}/{filename}"


class SubtitleList(models.Model):
    name = models.CharField(max_length=255, blank=True, default="")
    is_open_menu = models.BooleanField(default=False)
    is_hide = models.BooleanField(default=False)

    is_public = models.BooleanField(default=False)

    owner = models.ForeignKey(  # 👈 владелец списка
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="owned_subtitle_lists",
    )

    background_image = models.ImageField(
        upload_to=subtitle_list_image_path,
        null=True,
        blank=True,
    )

    background_color = models.CharField(
        max_length=20, default="#ffffff", help_text="CSS цвет фона (например: #ffffff)"
    )

    quantity_words = models.PositiveIntegerField(default=0)
    quantity_words_frequencies = models.PositiveIntegerField(default=0)
    quantity_learned_words = models.PositiveIntegerField(default=0)
    quantity_learned_words_frequencies = models.PositiveIntegerField(default=0)

    created_time = models.DateTimeField(auto_now_add=True)
    modified_time = models.DateTimeField(auto_now=True)

    users = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        through="UserSubtitleList",
        related_name="subtitle_lists",
    )

    words = models.ManyToManyField(
        "dictionary.Word",
        through="SubtitleListWord",
        related_name="subtitle_lists",
    )

    def __str__(self):
        return self.name


class UserSubtitleList(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    subtitle_list = models.ForeignKey(SubtitleList, on_delete=models.CASCADE)

    class Meta:
        unique_together = ("user", "subtitle_list")


class SubtitleListWord(models.Model):
    subtitle_list = models.ForeignKey(
        "lists.SubtitleList",
        on_delete=models.CASCADE,
        related_name="word_links",
    )
    word = models.ForeignKey(
        "dictionary.Word",
        on_delete=models.CASCADE,
        related_name="subtitle_links",
    )
    frequency = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("subtitle_list", "word")
