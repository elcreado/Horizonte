import json
from pathlib import Path

from django.test import SimpleTestCase

from config.api_inventory import build_inventory


class ApiInventoryTests(SimpleTestCase):
    def test_alias_contract_documents_source_and_existing_or_created_assignment(self):
        operations = build_inventory()["paths"]["/api/companies/{company_id}/merchant-aliases/"]
        post = operations["post"]
        schema = post["requestBody"]["content"]["application/json"]["schema"]
        self.assertEqual(set(schema["required"]), {"merchant_id", "provider", "name"})
        self.assertEqual(schema["properties"]["provider"]["enum"], ["manual_upload", "mock"])
        self.assertEqual(schema["properties"]["merchant_id"]["minimum"], 1)
        self.assertEqual(schema["properties"]["name"]["maxLength"], 250)
        self.assertNotIn("x-request-schema-pending", post)
        self.assertEqual(post["responses"]["200"]["content"], post["responses"]["201"]["content"])
        listed = operations["get"]["responses"]["200"]["content"]["application/json"]["schema"]
        self.assertEqual(listed["properties"]["results"]["maxItems"], 20)
        self.assertIn("can_edit", listed["required"])

    def test_import_contract_is_multipart_and_distinguishes_acceptance(self):
        paths = build_inventory()["paths"]
        operations = paths["/api/companies/{company_id}/imports/"]
        post = operations["post"]
        content = post["requestBody"]["content"]
        self.assertEqual(set(content), {"multipart/form-data"})
        fields = content["multipart/form-data"]["schema"]
        self.assertEqual(fields["required"], ["account_id", "file"])
        self.assertEqual(fields["properties"]["file"]["format"], "binary")
        job = post["responses"]["202"]["content"]["application/json"]["schema"]
        self.assertEqual(job["properties"]["status"]["enum"], ["queued", "completed", "failed"])
        self.assertNotIn("content", job["properties"])
        listed = operations["get"]["responses"]["200"]["content"]["application/json"]["schema"]
        self.assertEqual(listed["maxItems"], 20)
        self.assertEqual(listed["items"], job)
        self.assertIn("503", post["responses"])

    def test_balance_and_coverage_contracts_include_conflicts_and_nullable_dates(self):
        paths = build_inventory()["paths"]
        balance = paths["/api/companies/{company_id}/accounts/{account_id}/balance/"]["patch"]
        coverage = paths["/api/companies/{company_id}/accounts/{account_id}/coverage/"]["post"]
        for operation in (balance, coverage):
            self.assertNotIn("x-request-schema-pending", operation)
            self.assertEqual(
                set(operation["responses"]), {"200", "400", "403", "404", "409", "default"}
            )
            fields = operation["responses"]["200"]["content"]["application/json"]["schema"][
                "properties"
            ]
            self.assertTrue(fields["history_complete_from"]["nullable"])
        request = coverage["requestBody"]["content"]["application/json"]["schema"]
        self.assertEqual(request["properties"]["confirmed"], {"type": "boolean"})
        self.assertEqual(request["required"], ["start", "confirmed"])

    def test_onboarding_and_profile_match_serializer_constraints(self):
        paths = build_inventory()["paths"]
        register = paths["/api/auth/register/"]["post"]
        schema = register["requestBody"]["content"]["application/json"]["schema"]
        self.assertEqual(register["security"], [])
        self.assertIn("201", register["responses"])
        self.assertEqual(schema["properties"]["nit"]["pattern"], "^[A-Za-z0-9-]+$")
        self.assertEqual(schema["properties"]["balance_date"]["format"], "date")
        self.assertEqual(schema["properties"]["opening_balance"]["x-decimal-places"], 2)
        profile = paths["/api/auth/profile/"]["patch"]
        fields = profile["requestBody"]["content"]["application/json"]["schema"]
        self.assertEqual(fields["required"], ["current_password"])
        self.assertTrue(fields["properties"]["current_password"]["writeOnly"])
        self.assertEqual(
            paths["/api/companies/create/"]["post"]["security"], [{"sessionCookie": []}]
        )

    def test_auth_bodies_and_success_codes_are_documented(self):
        paths = build_inventory()["paths"]
        reset = paths["/api/auth/reset-password/"]["post"]
        schema = reset["requestBody"]["content"]["application/json"]["schema"]
        self.assertEqual(schema["properties"]["password"]["minLength"], 10)
        self.assertEqual(schema["properties"]["password"]["maxLength"], 128)
        self.assertNotIn("x-request-schema-pending", reset)
        self.assertIn("202", paths["/api/auth/recover-password/"]["post"]["responses"])
        self.assertNotIn("content", paths["/api/auth/logout/"]["post"]["responses"]["204"])

    def test_public_auth_is_distinguished_from_financial_session(self):
        paths = build_inventory()["paths"]
        self.assertEqual(paths["/api/auth/login/"]["post"]["security"], [])
        self.assertEqual(paths["/api/health/"]["get"]["security"], [])
        self.assertEqual(paths["/api/companies/"]["get"]["security"], [{"sessionCookie": []}])
        correct = paths["/api/companies/{company_id}/movements/{transaction_id}/category/"]["patch"]
        self.assertEqual(
            [parameter["name"] for parameter in correct["parameters"]],
            ["company_id", "transaction_id", "X-CSRFToken"],
        )
        self.assertNotIn("x-request-schema-pending", correct)
        body = correct["requestBody"]["content"]["application/json"]["schema"]
        self.assertEqual(body["required"], ["category"])
        self.assertEqual(body["properties"]["remember"], {"type": "boolean", "default": False})

    def test_saved_artifact_tracks_routes_without_duplicate_operation_ids(self):
        inventory = build_inventory()
        saved = json.loads(
            (Path(__file__).parents[2] / "docs" / "openapi-inventory.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(saved, inventory)
        identifiers = [
            operation["operationId"]
            for route in inventory["paths"].values()
            for operation in route.values()
        ]
        self.assertEqual(len(identifiers), len(set(identifiers)))
