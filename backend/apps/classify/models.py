from django.conf import settings
from django.db import models


class ClassificationRule(models.Model):
    company = models.ForeignKey("accounts.Company", on_delete=models.CASCADE)
    normalized_description = models.CharField(max_length=250)
    direction = models.CharField(max_length=3)
    category = models.CharField(max_length=80)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["company", "normalized_description", "direction"],
                name="unique_company_rule",
            )
        ]


class ClassificationChange(models.Model):
    transaction = models.ForeignKey("banking.Transaction", on_delete=models.PROTECT)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    previous_category = models.CharField(max_length=80)
    category = models.CharField(max_length=80)
    remembered = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
