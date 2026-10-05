from django.test import TestCase
from rest_framework.test import APIClient

from config.api_inventory import build_inventory


class AuthErrorContractTests(TestCase):
    def test_login_validation_and_unsupported_content_codes(self):
        client = APIClient()
        operation = build_inventory()["paths"]["/api/auth/login/"]["post"]
        missing = client.post("/api/auth/login/", {"username": "synthetic"}, format="json")
        self.assertEqual(missing.status_code, 400)
        self.assertIsInstance(missing.json()["detail"], str)
        self.assertIn("400", operation["responses"])
        unsupported = client.post(
            "/api/auth/login/", data="synthetic", content_type="application/octet-stream"
        )
        self.assertEqual(unsupported.status_code, 415)
        schema = operation["responses"]["415"]["content"]["application/json"]["schema"]
        self.assertEqual(set(unsupported.json()), set(schema["properties"]))

    def test_anonymous_protected_queries_return_documented_json(self):
        client = APIClient()
        paths = build_inventory()["paths"]
        for path in ("/api/auth/me/", "/api/auth/profile/"):
            with self.subTest(path=path):
                response = client.get(path)
                self.assertEqual(response.status_code, 403)
                schema = paths[path]["get"]["responses"]["403"]["content"]["application/json"][
                    "schema"
                ]
                self.assertEqual(set(response.json()), set(schema["properties"]))

    def test_public_csrf_rejection_is_documented_as_html(self):
        client = APIClient(enforce_csrf_checks=True)
        response = client.post(
            "/api/auth/login/", {"username": "synthetic", "password": "invalid"}, format="json"
        )
        self.assertEqual(response.status_code, 403)
        self.assertTrue(response["Content-Type"].startswith("text/html"))
        operation = build_inventory()["paths"]["/api/auth/login/"]["post"]
        self.assertIn("text/html", operation["responses"]["403"]["content"])
        self.assertIn("Retry-After", operation["responses"]["429"]["headers"])
