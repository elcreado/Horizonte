from django.db import models

from apps.accounts.models import Company


class Obligation(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    counterparty = models.CharField(max_length=200, blank=True)
    cancelled = models.BooleanField(default=False)
    reference = models.CharField(max_length=120)
    description = models.CharField(max_length=200)
    direction = models.CharField(max_length=3, choices=[("in", "Cobro"), ("out", "Pago")])
    due_date = models.DateField()
    outstanding_amount = models.DecimalField(max_digits=18, decimal_places=2)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["company", "reference"], name="unique_obligation"),
            models.CheckConstraint(
                condition=models.Q(outstanding_amount__gte=0),
                name="positive_outstanding",
            ),
        ]


class Settlement(models.Model):
    obligation = models.ForeignKey(Obligation, on_delete=models.PROTECT, related_name="settlements")
    transaction = models.ForeignKey(
        "banking.Transaction", on_delete=models.PROTECT, related_name="settlements"
    )
    user = models.ForeignKey("auth.User", on_delete=models.PROTECT)
    amount = models.DecimalField(max_digits=18, decimal_places=2)
    request_id = models.UUIDField()
    created_at = models.DateTimeField(auto_now_add=True)
    reversed_at = models.DateTimeField(null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["obligation", "request_id"], name="unique_settlement_attempt"
            ),
            models.CheckConstraint(condition=models.Q(amount__gt=0), name="positive_settlement"),
        ]


class RecurrenceReview(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE)
    fingerprint = models.CharField(max_length=64)
    status = models.CharField(
        max_length=12,
        choices=[("confirmed", "Confirmada"), ("rejected", "Rechazada"), ("pending", "Pendiente")],
    )
    evidence = models.JSONField()
    user = models.ForeignKey("auth.User", on_delete=models.PROTECT)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["company", "fingerprint"], name="unique_recurrence_review"
            )
        ]


class RecurrenceOccurrence(models.Model):
    company = models.ForeignKey(Company, on_delete=models.PROTECT)
    key = models.CharField(max_length=64)
    obligation = models.OneToOneField(Obligation, on_delete=models.PROTECT)
    review = models.ForeignKey(RecurrenceReview, on_delete=models.PROTECT)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["company", "key"], name="unique_recurrence_occurrence")
        ]
