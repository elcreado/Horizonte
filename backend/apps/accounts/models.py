from django.conf import settings
from django.db import models


class Company(models.Model):
    name = models.CharField(max_length=200)
    nit = models.CharField(max_length=30, unique=True)


class CompanyMember(models.Model):
    class Role(models.TextChoices):
        OWNER = "owner", "Propietario"
        ACCOUNTANT = "accountant", "Contador"
        VIEWER = "viewer", "Consulta"

    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name="members")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=16, choices=Role.choices)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["company", "user"], name="unique_membership")
        ]


class AuditLog(models.Model):
    company = models.ForeignKey(Company, on_delete=models.PROTECT)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    action = models.CharField(max_length=80)
    entity = models.CharField(max_length=80)
    entity_id = models.CharField(max_length=80)
    before = models.JSONField(default=dict)
    after = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
