from django.contrib.auth import authenticate, login, logout
from django.http import JsonResponse
from django.middleware.csrf import get_token
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_GET
from rest_framework.decorators import api_view, permission_classes, throttle_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response

from .models import Company
from .throttles import PersistentUserThrottle


class LoginThrottle(PersistentUserThrottle):
    scope = "login"


@require_GET
def csrf(request):
    return JsonResponse({"csrfToken": get_token(request)})


@api_view(["POST"])
@permission_classes([AllowAny])
@throttle_classes([LoginThrottle])
@csrf_protect
def login_view(request):
    username = request.data.get("username")
    password = request.data.get("password")
    if not isinstance(username, str) or not isinstance(password, str):
        return Response({"detail": "Usuario y contraseña requeridos."}, status=400)
    user = authenticate(request, username=username, password=password)
    if user is None:
        return Response({"detail": "Credenciales incorrectas."}, status=400)
    login(request, user)
    return Response({"username": user.username})


@api_view(["POST"])
def logout_view(request):
    logout(request)
    return Response(status=204)


@api_view(["GET"])
def me(request):
    user = request.user
    return Response(
        {
            "username": user.username,
            "platform_admin": bool(user.is_active and user.is_staff and user.is_superuser),
        }
    )


@api_view(["GET"])
def companies(request):
    return Response(list(Company.objects.filter(members__user=request.user).values("id", "name")))
