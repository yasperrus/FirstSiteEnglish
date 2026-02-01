from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.lists.urls")),
    path("dictionary/", include("apps.dictionary.urls")),
    path("study/", include("apps.study.urls")),
    path("social/", include("apps.social.urls")),
    path("ingestion/", include("apps.ingestion.urls")),
    path("video/", include("apps.video.urls")),
    path("accounts/", include("apps.accounts.urls")),
]
