"""Las operaciones de empresa deben rechazar sesiones ajenas o ausentes."""

import re

from django.contrib.auth import get_user_model
from django.test import TestCase
from rest_framework.test import APIClient

from apps.accounts.models import Company, CompanyMember
from config.api_inventory import build_inventory


class ReadAccessMatrixTests(TestCase):
    def test_every_company_get_rejects_another_tenant_and_anonymous_session(self):
        own = Company.objects.create(name="Own", nit="read-matrix-own")
        foreign = Company.objects.create(name="Foreign", nit="read-matrix-foreign")
        user = get_user_model().objects.create_user("read-matrix-user")
        CompanyMember.objects.create(company=own, user=user, role="owner")
        client = APIClient()
        checked = []
        for path, operations in build_inventory()["paths"].items():
            if "{company_id}" not in path or "get" not in operations:
                continue
            url = re.sub(r"\{[^}]+\}", "1", path.replace("{company_id}", str(foreign.pk)))
            with self.subTest(path=path, session="foreign"):
                client.force_authenticate(user)
                self.assertEqual(client.get(url).status_code, 404)
            with self.subTest(path=path, session="anonymous"):
                client.force_authenticate(None)
                self.assertEqual(client.get(url).status_code, 403)
            checked.append(path)
        self.assertGreaterEqual(len(checked), 20)

    def test_company_mutations_reject_foreign_and_anonymous_sessions(self):
        own = Company.objects.create(name="Own", nit="write-matrix-own")
        foreign = Company.objects.create(name="Foreign", nit="write-matrix-foreign")
        user = get_user_model().objects.create_user("write-matrix-user")
        CompanyMember.objects.create(company=own, user=user, role="owner")
        client = APIClient()
        checked = []
        for path, operations in build_inventory()["paths"].items():
            if "{company_id}" not in path:
                continue
            url = re.sub(r"\{[^}]+\}", "1", path.replace("{company_id}", str(foreign.pk)))
            for method in ("post", "patch", "put", "delete"):
                if method not in operations:
                    continue
                with self.subTest(path=path, method=method, session="foreign"):
                    client.force_authenticate(user)
                    response = getattr(client, method)(url, {}, format="json")
                    self.assertIn(response.status_code, (403, 404))
                with self.subTest(path=path, method=method, session="anonymous"):
                    client.force_authenticate(None)
                    self.assertEqual(
                        getattr(client, method)(url, {}, format="json").status_code, 403
                    )
                checked.append((path, method))
        self.assertGreaterEqual(len(checked), 20)
