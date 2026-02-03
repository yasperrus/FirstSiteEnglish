from django.db import models
from django.conf import settings


class KnownWord(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="known_words"
    )
    word = models.ForeignKey(
        "dictionary.Word", on_delete=models.CASCADE, related_name="known_by_users"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "study_usersknownwords"
        unique_together = ("user", "word")
