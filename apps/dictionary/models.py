from django.db import models


class Word(models.Model):
    name = models.CharField(
        max_length=128, unique=True, db_index=True, null=True, blank=True
    )
    transcription = models.CharField(max_length=128, blank=True, default="")

    def __str__(self):
        return self.name

    class Meta:
        db_table = "dictionary_words"


class PartOfSpeech(models.Model):
    name = models.CharField(max_length=128)
    is_main = models.BooleanField(default=False)

    word = models.ForeignKey(
        "dictionary.Word",
        on_delete=models.CASCADE,
        related_name="parts_of_speech",
    )

    def __str__(self):
        return f"{self.word.name} — {self.name}"

    class Meta:
        db_table = "dictionary_parts_of_speech"


class Translation(models.Model):
    translation = models.CharField(max_length=255, blank=True, default="")
    is_main = models.BooleanField(default=False)

    part_of_speech = models.ForeignKey(
        "dictionary.PartOfSpeech",
        on_delete=models.CASCADE,
        related_name="translations",
        null=True,  # 👈 временно
        blank=True,
    )

    def __str__(self):
        return self.translation

    class Meta:
        db_table = "dictionary_translations"
