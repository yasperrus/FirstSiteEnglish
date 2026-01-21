from django.contrib.auth.decorators import login_required
from django.contrib.auth.views import LogoutView
from django.urls import path, include

from accounts.views import (
    login_ajax,
    register_ajax,
    logout_ajax,
    profile_view,
    login_page,
)

urlpatterns = [
    path("accounts/", include("allauth.urls")),
    path("login/", login_page, name="login"),
    path("login/ajax/", login_ajax, name="login_ajax"),
    path("register/ajax/", register_ajax, name="register_ajax"),
    path("logout/ajax/", logout_ajax, name="logout_ajax"),
    path('profile/', login_required(profile_view), name='profile'),
    # path("profile/", profile, name="profile"),
]
