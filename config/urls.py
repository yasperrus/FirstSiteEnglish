from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path("", include("apps.lists.urls")),
    path("video/", include("apps.video.urls")),
    path("accounts/", include("apps.accounts.urls")),
]
