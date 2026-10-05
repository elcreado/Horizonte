"""Entrega de correo por HTTPS para alojamientos que bloquean SMTP."""

import json
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from django.conf import settings
from django.core.mail.backends.base import BaseEmailBackend


class EmailBackend(BaseEmailBackend):
    def send_messages(self, email_messages):
        sent = 0
        for message in email_messages or []:
            if not message.recipients():
                continue
            try:
                if not settings.RESEND_API_KEY:
                    raise ValueError("Falta configurar RESEND_API_KEY.")
                if message.attachments or getattr(message, "alternatives", []):
                    raise ValueError(
                        "Este backend admite únicamente mensajes de texto sin adjuntos."
                    )
                payload = {
                    "from": message.from_email,
                    "to": message.to,
                    "subject": message.subject,
                    "text": message.body,
                }
                if message.cc:
                    payload["cc"] = message.cc
                if message.bcc:
                    payload["bcc"] = message.bcc
                if message.reply_to:
                    payload["reply_to"] = message.reply_to
                request = Request(
                    "https://api.resend.com/emails",
                    data=json.dumps(payload).encode("utf-8"),
                    headers={
                        "Authorization": f"Bearer {settings.RESEND_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    method="POST",
                )
                with urlopen(request, timeout=settings.EMAIL_TIMEOUT) as response:
                    result = json.loads(response.read(65536))
                if not isinstance(result, dict) or not result.get("id"):
                    raise ValueError("El proveedor no confirmó la aceptación del correo.")
                sent += 1
            except (HTTPError, URLError, OSError, ValueError):
                if not self.fail_silently:
                    # Nunca incluir la respuesta del proveedor, el token ni el enlace de recuperación.
                    raise RuntimeError(
                        "No fue posible entregar el correo al proveedor HTTPS."
                    ) from None
        return sent
