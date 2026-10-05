import json
from unittest.mock import MagicMock, patch
from urllib.error import HTTPError

from django.core.mail import EmailMessage
from django.test import SimpleTestCase, override_settings

from config.email import EmailBackend


@override_settings(RESEND_API_KEY="test-secret", EMAIL_TIMEOUT=10)
class HttpsEmailTests(SimpleTestCase):
    def message(self):
        return EmailMessage("Recuperación", "Enlace privado", "demo@example.com", ["a@example.com"])

    @patch("config.email.urlopen")
    def test_https_payload_and_acceptance(self, open_url):
        response = MagicMock()
        response.read.return_value = b'{"id":"accepted"}'
        open_url.return_value.__enter__.return_value = response
        self.assertEqual(EmailBackend().send_messages([self.message()]), 1)
        request = open_url.call_args.args[0]
        self.assertEqual(request.full_url, "https://api.resend.com/emails")
        self.assertEqual(json.loads(request.data)["text"], "Enlace privado")
        self.assertEqual(open_url.call_args.kwargs["timeout"], 10)

    @patch("config.email.urlopen")
    def test_provider_failure_is_sanitized_and_can_retry(self, open_url):
        open_url.side_effect = HTTPError("private-token", 429, "private-link", {}, None)
        with self.assertRaisesRegex(RuntimeError, "proveedor HTTPS") as error:
            EmailBackend().send_messages([self.message()])
        self.assertNotIn("private", str(error.exception))
        self.assertEqual(EmailBackend(fail_silently=True).send_messages([self.message()]), 0)

    @override_settings(RESEND_API_KEY="")
    @patch("config.email.urlopen")
    def test_missing_key_never_sends(self, open_url):
        with self.assertRaises(RuntimeError):
            EmailBackend().send_messages([self.message()])
        open_url.assert_not_called()

    @patch("config.email.urlopen")
    def test_missing_acceptance_is_failure(self, open_url):
        open_url.return_value.__enter__.return_value.read.return_value = b"{}"
        with self.assertRaises(RuntimeError):
            EmailBackend().send_messages([self.message()])

    @patch("config.email.urlopen")
    def test_empty_recipients_skip_request(self, open_url):
        self.assertEqual(EmailBackend().send_messages([EmailMessage("", "", "a@b.co", [])]), 0)
        open_url.assert_not_called()
