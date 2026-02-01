from django.urls import path
from django.views.generic import TemplateView

from apps.ingestion.views import SubtitlePreviewView, SaveSubtitleListView

app_name = "ingestion"

urlpatterns = [
    path("subtitle/preview/", SubtitlePreviewView.as_view(), name="subtitle_preview"),
    path("subtitle/save/", SaveSubtitleListView.as_view(), name="subtitle_save"),
    path(
        "subtitle/add/",
        TemplateView.as_view(template_name="ingestion/subtitle_add.html"),
        name="subtitle_add",
    ),
]
