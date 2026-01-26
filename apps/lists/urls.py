from django.conf import settings
from django.conf.urls.static import static
from django.urls import path
from django.views.generic import TemplateView

from . import views
from .views import (
    SubtitlePreviewView,
    SaveSubtitleListView,
    ToggleKnownWordView,
    KnownWordsView,
)

urlpatterns = [
    path("", views.public_lists, name="public_lists"),
    path("my-lists/", views.my_lists, name="my_lists"),

    path("list/<int:list_id>/delete/", views.delete_list, name="delete_list"),
    path("list/edit/<int:list_id>/", views.word_list_edit, name="word_list_edit"),
    path("about/", views.about, name="about"),
    path("list/<int:list_id>/", views.word_list_detail, name="word_list_detail"),
    path(
        "translations/<word_id>/?part=<part_id>",
        views.get_translations,
        name="get_translations",
    ),
    path(
        "subtitle/add/",
        TemplateView.as_view(template_name="lists/subtitle_add.html"),
        name="subtitle_add",
    ),
    path("subtitle/preview/", SubtitlePreviewView.as_view(), name="subtitle_preview"),
    path("subtitle/save/", SaveSubtitleListView.as_view(), name="subtitle_save"),

    path('<int:list_id>/', views.study_cards, name='study_cards'),
    path(
            "lists/<int:pk>/toggle-publish/",
            views.toggle_publish,
            name="toggle_publish"
        ),
    path(
        "lists/<int:pk>/toggle-like/",
        views.toggle_like,
        name="toggle_like"
    ),
    path("list/<int:list_id>/mini-cards/", views.word_mini_cards, name="word_mini_cards"),
    path("known-words/", KnownWordsView.as_view(), name="known_words"),
    path("toggle-known-word/", ToggleKnownWordView.as_view(), name="toggle_known_word"),
    path("dictionary/", views.dictionary_view, name="dictionary"),
    path("api/dictionary/", views.dictionary_api, name="dictionary_api"),

    path(
        "list/<int:list_id>/download/",
        views.download_words,
        name="download_words"
    )

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
