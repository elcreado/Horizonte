from pathlib import Path
from tempfile import TemporaryDirectory

from django.test import TestCase, override_settings


class WebDeliveryTests(TestCase):
    def test_public_frontend_requires_no_session_and_is_not_cached(self):
        with TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "index.html").write_text("<html>Inicio público</html>", encoding="utf-8")
            with override_settings(FRONTEND_DIST=root):
                response = self.client.get("/")
                self.assertEqual(response.status_code, 200)
                self.assertIn("Inicio público", b"".join(response.streaming_content).decode())
                self.assertEqual(response["Cache-Control"], "no-store")

    def test_missing_build_is_explicit_and_financial_api_stays_private(self):
        with TemporaryDirectory() as directory, override_settings(FRONTEND_DIST=Path(directory)):
            self.assertEqual(self.client.get("/").status_code, 503)
        self.assertIn(self.client.get("/api/companies/").status_code, (401, 403))

    def test_health_and_production_headers(self):
        with override_settings(DEBUG=False, SECURE_SSL_REDIRECT=False):
            response = self.client.get("/api/health/")
            self.assertEqual(response.json(), {"status": "ok"})
            self.assertIn("frame-ancestors 'none'", response["Content-Security-Policy"])
