from django.apps import AppConfig


class IngestionConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.ingestion"

    def ready(self):
        from .services.nlp_loader import load_nlp

        load_nlp()
