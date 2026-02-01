from django.urls import path

from apps.social import views

app_name = "social"

urlpatterns = [
    path("lists/<int:pk>/toggle-like/", views.toggle_like, name="toggle_like"),
]
