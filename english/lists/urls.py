from django.urls import path
from django.views.generic import TemplateView

from . import views
from .views import SubtitlePreviewView, SaveSubtitleListView

urlpatterns = [
    path("", views.word_lists, name="word_lists"),
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
]
