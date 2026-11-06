import os
import runpy
from pathlib import Path
from unittest.mock import patch

from django.test import SimpleTestCase


class ProductionSettingsTests(SimpleTestCase):
    def load(self, **values):
        with patch.dict(os.environ, values, clear=True):
            return runpy.run_path(str(Path(__file__).parents[1] / "config" / "settings.py"))

    def production(self, **changes):
        values = {
            "DJANGO_DEBUG": "0",
            "DJANGO_SECRET_KEY": "test-only-production-key",
            "POSTGRES_HOST": "pooler.example.com",
            "POSTGRES_PASSWORD": "test-only-password",
            "FRONTEND_URL": "https://horizonte.example.com",
        }
        values.update(changes)
        return values

    def test_production_cannot_fall_back_to_ephemeral_sqlite(self):
        with self.assertRaisesRegex(RuntimeError, "POSTGRES_HOST"):
            self.load(**self.production(POSTGRES_HOST=""))

    def test_recovery_origin_rejects_local_http_secrets_and_paths(self):
        for origin in (
            "http://example.com",
            "https://localhost",
            "https://127.0.0.1",
            "https://u:secret@example.com",
            "https://example.com/app",
            "https://example.com?secret=x",
            "https://example.com/#/",
        ):
            with self.subTest(origin=origin), self.assertRaisesRegex(RuntimeError, "FRONTEND_URL"):
                self.load(**self.production(FRONTEND_URL=origin))

    def test_render_origin_is_used_without_explicit_frontend_url(self):
        values = self.production()
        del values["FRONTEND_URL"]
        values["RENDER_EXTERNAL_URL"] = "https://horizonte.onrender.com"
        loaded = self.load(**values)
        self.assertEqual(loaded["FRONTEND_URL"], values["RENDER_EXTERNAL_URL"])
        self.assertEqual(loaded["DATABASES"]["default"]["ENGINE"], "django.db.backends.postgresql")

    def test_local_development_still_works_without_external_services(self):
        loaded = self.load()
        self.assertTrue(loaded["DEBUG"])
        self.assertEqual(loaded["DATABASES"]["default"]["ENGINE"], "django.db.backends.sqlite3")
