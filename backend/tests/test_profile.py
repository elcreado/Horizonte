from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient


class ProfileTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="profile", password="Previous-72!secret", email="old@example.test"
        )
        self.client = APIClient()
        self.client.login(username="profile", password="Previous-72!secret")

    def test_change_password_retains_current_session_revokes_other(self):
        other = APIClient()
        other.login(username="profile", password="Previous-72!secret")
        response = self.client.patch(
            "/api/auth/profile/",
            {
                "current_password": "Previous-72!secret",
                "email": "new@example.test",
                "password": "Updated-37!secure",
                "password_confirm": "Updated-37!secure",
            },
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.get("/api/auth/me/").status_code, 200)
        self.assertIn(other.get("/api/auth/me/").status_code, [401, 403])
        self.user.refresh_from_db()
        self.assertTrue(self.user.check_password("Updated-37!secure"))
        self.assertEqual(self.user.email, "new@example.test")

    def test_invalid_password_does_not_change_email(self):
        for password, new in [("wrong", "Updated-37!secure"), ("Previous-72!secret", "1234567890")]:
            response = self.client.patch(
                "/api/auth/profile/",
                {
                    "current_password": password,
                    "email": "new@example.test",
                    "password": new,
                    "password_confirm": new,
                },
                format="json",
            )
            self.assertEqual(response.status_code, 400)
            self.user.refresh_from_db()
            self.assertEqual(self.user.email, "old@example.test")
        self.client.logout()
        self.assertIn(self.client.get("/api/auth/profile/").status_code, [401, 403])
