from django.urls import path

from apps.study import views
from apps.study.views import ToggleKnownWordView, KnownWordsView

app_name = "study"

urlpatterns = [
    path(
        "study/<int:list_id>/mini-cards/", views.word_mini_cards, name="word_mini_cards"
    ),
    path("known-words/", KnownWordsView.as_view(), name="known_words"),
    path("toggle-known-word/", ToggleKnownWordView.as_view(), name="toggle_known_word"),
    path("<int:list_id>/", views.study_cards, name="study_cards"),
]
