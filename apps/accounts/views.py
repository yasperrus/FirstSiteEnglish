from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.http import require_POST


def login_page(request):
    return render(request, "accounts/login.html")

def login_ajax(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    username = request.POST.get("username")
    password = request.POST.get("password")

    user = authenticate(request, username=username, password=password)
    if user is not None:
        login(request, user)
        return JsonResponse({"success": True})
    else:
        return JsonResponse({"error": "Неверный логин или пароль"}, status=400)

def register_ajax(request):
    if request.method != "POST":
        return JsonResponse({"error": "Invalid method"}, status=405)

    username = request.POST.get("username")
    email = request.POST.get("email")
    password = request.POST.get("password")

    # Проверка обязательных полей
    if not username or not email or not password:
        return JsonResponse({"error": "Все поля обязательны"}, status=400)

    # Проверка на существующего пользователя
    if User.objects.filter(username=username).exists():
        return JsonResponse({"error": "Пользователь с таким именем уже существует"}, status=400)

    # Создаём пользователя
    User.objects.create_user(username=username, email=email, password=password)

    # Аутентификация, чтобы правильно определить backend
    user = authenticate(username=username, password=password)
    if user is not None:
        login(request, user)
        return JsonResponse({"success": True})
    else:
        return JsonResponse({"error": "Ошибка авторизации"}, status=400)

@require_POST
def logout_ajax(request):
    logout(request)
    return JsonResponse({"success": True})

@login_required
def profile_view(request):
    return render(request, "accounts/profile.html")
