from django.conf import settings
from django.contrib.auth import get_user_model
from django.contrib.auth.tokens import default_token_generator
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.utils.http import urlsafe_base64_encode

from config.celery import app


@app.task
def send_password_recovery(username: str, email: str) -> None:
    user = (
        get_user_model()
        .objects.filter(username=username, email__iexact=email, is_active=True)
        .first()
    )
    if not user or not user.has_usable_password():
        return
    uid = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    link = f"{settings.FRONTEND_URL.rstrip('/')}/#/reset-password?uid={uid}&token={token}"
    send_mail(
        "Restablecer contraseña de Horizonte",
        f"Solicitaste restablecer tu contraseña. Abre este enlace:\n\n{link}\n\n"
        "El enlace vence en una hora y deja de funcionar al cambiar tu contraseña. "
        "Si no hiciste esta solicitud, puedes ignorar este mensaje.",
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False,
    )
