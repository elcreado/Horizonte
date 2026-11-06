from django.test import TestCase

from apps.accounts.models import Company
from apps.banking.models import BankAccount, Transaction
from config.api_inventory import build_inventory
from tests.test_imports import ImportTests


class CategorySuggestionTests(TestCase):
    setUp = ImportTests.setUp

    def test_other_company_labels_cannot_train_or_expose_a_suggestion(self):
        other = Company.objects.create(name="Other", nit="other-suggestion")
        account = BankAccount.objects.create(
            company=other, name="Other", balance=0, balance_date=self.account.balance_date
        )
        for category, text in (("Software", "LICENCIA DIGITAL"), ("Transporte", "BUS PASAJE")):
            for suffix in ("ALFA", "BETA", "GAMA"):
                Transaction.objects.create(
                    account=account,
                    external_id=f"{text}-{suffix}",
                    date=account.balance_date,
                    amount=-10,
                    description=f"{text} {suffix}",
                    category=category,
                    classification_source="manual",
                )
        target = Transaction.objects.create(
            account=self.account,
            external_id="target-own",
            date=self.account.balance_date,
            amount=-10,
            description="LICENCIA DIGITAL NUEVA",
            category="Otros",
        )
        url = f"/api/companies/{self.company.pk}/movements/{target.pk}/category-suggestion/"
        self.assertEqual(self.client.get(url).status_code, 409)
        foreign = Transaction.objects.filter(account=account).first()
        self.assertEqual(
            self.client.get(
                url.replace(f"movements/{target.pk}", f"movements/{foreign.pk}")
            ).status_code,
            404,
        )
        self.assertEqual(
            self.client.get(
                url.replace(f"companies/{self.company.pk}", f"companies/{other.pk}")
            ).status_code,
            404,
        )

    def test_manual_training_suggests_without_mutation_and_other_tenant_is_rejected(self):
        for category, text in (("Software", "LICENCIA DIGITAL"), ("Transporte", "BUS PASAJE")):
            for suffix in ("ALFA", "BETA", "GAMA"):
                Transaction.objects.create(
                    account=self.account,
                    external_id=f"{text}-{suffix}",
                    date=self.account.balance_date,
                    amount=-10,
                    description=f"{text} {suffix}",
                    category=category,
                    classification_source="manual",
                )
        target = Transaction.objects.create(
            account=self.account,
            external_id="target",
            date=self.account.balance_date,
            amount=-10,
            description="LICENCIA DIGITAL NUEVA",
            category="Otros",
        )
        url = f"/api/companies/{self.company.pk}/movements/{target.pk}/category-suggestion/"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        operation = build_inventory()["paths"][
            "/api/companies/{company_id}/movements/{transaction_id}/category-suggestion/"
        ]["get"]
        schema = operation["responses"]["200"]["content"]["application/json"]["schema"]
        self.assertEqual(set(response.json()), set(schema["properties"]))
        self.assertEqual(response.data["category"], "Software")
        target.refresh_from_db()
        self.assertEqual(target.category, "Otros")
        target.description = "ZZZXQ WVVVXQ"
        target.save(update_fields=["description"])
        abstained = self.client.get(url)
        self.assertEqual(abstained.status_code, 200)
        self.assertEqual(abstained.json()["status"], "abstained")
        self.assertIsNone(abstained.json()["category"])
        self.assertEqual(set(abstained.json()), set(schema["properties"]))
        self.assertEqual(
            self.client.get(
                url.replace(f"companies/{self.company.pk}", "companies/999999")
            ).status_code,
            404,
        )
        Transaction.objects.filter(classification_source="manual").update(
            classification_source="rule"
        )
        self.assertEqual(self.client.get(url).status_code, 409)
