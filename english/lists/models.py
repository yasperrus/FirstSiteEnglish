from django.conf import settings
from django.contrib.auth.models import User
from django.db import models

# Create your models here.
from django.db import models

class SubtitleList(models.Model):
    name = models.CharField(max_length=255, blank=True, default="")
    is_open_menu = models.BooleanField(default=False)
    is_hide = models.BooleanField(default=False)

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
        "Word",
        through="SubtitleListWord",
        related_name="subtitle_lists",
    )

    def __str__(self):
        return self.name

class UserSubtitleList(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE
    )
    subtitle_list = models.ForeignKey(
        SubtitleList,
        on_delete=models.CASCADE
    )

    class Meta:
        unique_together = ("user", "subtitle_list")

class SubtitleListWord(models.Model):
    subtitle_list = models.ForeignKey(
        SubtitleList,
        on_delete=models.CASCADE,
        related_name="word_links",
    )
    word = models.ForeignKey(
        "Word",
        on_delete=models.CASCADE,
        related_name="subtitle_links",
    )
    frequency = models.PositiveIntegerField(default=1)

    class Meta:
        unique_together = ("subtitle_list", "word")

class Word(models.Model):
    name = models.CharField(max_length=255, unique=True,null=True, blank=True)
    transcription = models.CharField(max_length=30, blank=True, default="")

    def __str__(self):
        return self.name

class PathOfSpeech(models.Model):
    name = models.CharField(max_length=100)
    is_main = models.BooleanField(default=False)

    word = models.ForeignKey(
        Word,
        on_delete=models.CASCADE,
        related_name="parts_of_speech",
    )

    def __str__(self):
        return f"{self.word.name} — {self.name}"


class Translation(models.Model):
    translation = models.CharField(max_length=255, blank=True, default="")
    is_main = models.BooleanField(default=False)

    path_of_speech = models.ForeignKey(
        PathOfSpeech,
        on_delete=models.CASCADE,
        related_name="translations",
        null=True,  # 👈 временно
        blank=True,
    )

    def __str__(self):
        return self.translation
