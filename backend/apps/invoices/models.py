from django.conf import settings
from django.db import models


class Invoice(models.Model):
    company = models.ForeignKey("accounts.Company", on_delete=models.PROTECT)
    cufe = models.CharField(max_length=150)
    number = models.CharField(max_length=100)
    direction = models.CharField(max_length=3)
    data = models.JSONField()
    obligation = models.OneToOneField("forecast.Obligation", null=True, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["company", "cufe"], name="unique_invoice_cufe")
        ]


class InvoiceImport(models.Model):
    company = models.ForeignKey("accounts.Company", on_delete=models.PROTECT)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    content = models.TextField()
    status = models.CharField(max_length=12, default="queued")
    error = models.CharField(max_length=300, blank=True)
    invoice = models.ForeignKey(Invoice, null=True, on_delete=models.PROTECT)
    duplicate = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    finished_at = models.DateTimeField(null=True)
