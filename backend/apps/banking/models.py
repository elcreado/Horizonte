from django.db import models

from apps.accounts.models import Company


class BankAccount(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    name = models.CharField(max_length=120)
    currency = models.CharField(max_length=3, default="COP", choices=[("COP", "COP")])
    balance = models.DecimalField(max_digits=18, decimal_places=2)
    balance_date = models.DateField()
    history_complete_from = models.DateField(null=True, blank=True)
    history_complete_through = models.DateField(null=True, blank=True)
    history_confirmed_at = models.DateTimeField(null=True, blank=True)
    history_confirmed_by = models.ForeignKey(
        "auth.User", null=True, blank=True, on_delete=models.SET_NULL
    )
    connection = models.OneToOneField(
        "BankConnection", null=True, blank=True, on_delete=models.PROTECT
    )


class BankConsent(models.Model):
    company = models.ForeignKey(Company, on_delete=models.PROTECT)
    user = models.ForeignKey("auth.User", on_delete=models.PROTECT)
    scopes = models.JSONField(default=list)
    granted_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True)


class BankConnection(models.Model):
    company = models.ForeignKey(Company, on_delete=models.PROTECT)
    consent = models.OneToOneField(BankConsent, on_delete=models.PROTECT)
    provider = models.CharField(max_length=40)
    status = models.CharField(max_length=12, default="active")
    created_at = models.DateTimeField(auto_now_add=True)
    revoked_at = models.DateTimeField(null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["company", "provider"],
                condition=models.Q(status="active"),
                name="unique_active_bank_provider",
            )
        ]


class BankSyncJob(models.Model):
    connection = models.ForeignKey(BankConnection, on_delete=models.PROTECT)
    user = models.ForeignKey("auth.User", on_delete=models.PROTECT)
    status = models.CharField(max_length=12, default="queued")
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True)
    created_count = models.PositiveIntegerField(default=0)
    duplicate_count = models.PositiveIntegerField(default=0)
    error = models.CharField(max_length=300, blank=True)


class Merchant(models.Model):
    company = models.ForeignKey(Company, on_delete=models.PROTECT)
    normalized_name = models.CharField(max_length=250)
    display_name = models.CharField(max_length=250)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["company", "normalized_name"], name="unique_company_merchant"
            )
        ]


class MerchantAlias(models.Model):
    company = models.ForeignKey(Company, on_delete=models.PROTECT)
    merchant = models.ForeignKey(Merchant, on_delete=models.PROTECT)
    provider = models.CharField(max_length=40)
    normalized_name = models.CharField(max_length=250)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["company", "provider", "normalized_name"],
                name="unique_provider_merchant_alias",
            )
        ]


class Transaction(models.Model):
    account = models.ForeignKey(BankAccount, on_delete=models.CASCADE)
    external_id = models.CharField(max_length=120)
    date = models.DateField()
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    description = models.CharField(max_length=250)
    normalized_description = models.TextField(blank=True)
    merchant_name = models.CharField(max_length=250, blank=True)
    merchant = models.ForeignKey(Merchant, null=True, blank=True, on_delete=models.PROTECT)
    category = models.CharField(max_length=80, default="Otros")
    classification_source = models.CharField(max_length=16, default="existing")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["account", "external_id"], name="unique_transaction")
        ]


class ImportJob(models.Model):
    file_format = models.CharField(
        max_length=4, default="csv", choices=[("csv", "CSV"), ("xlsx", "XLSX")]
    )
    account = models.ForeignKey(BankAccount, on_delete=models.PROTECT)
    user = models.ForeignKey("auth.User", on_delete=models.PROTECT)
    checksum = models.CharField(max_length=64)
    content = models.TextField()
    status = models.CharField(
        max_length=12,
        default="queued",
        choices=[("queued", "En cola"), ("completed", "Completado"), ("failed", "Fallido")],
    )
    created_count = models.PositiveIntegerField(default=0)
    duplicate_count = models.PositiveIntegerField(default=0)
    error = models.CharField(max_length=300, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True)
