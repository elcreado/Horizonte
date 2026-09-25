from decimal import Decimal

from rest_framework import serializers

from .models import Obligation


class ObligationInput(serializers.Serializer):
    reference = serializers.CharField(max_length=120)
    description = serializers.CharField(max_length=200)
    counterparty = serializers.CharField(max_length=200, required=False, allow_blank=True)
    direction = serializers.ChoiceField(choices=["in", "out"])
    due_date = serializers.DateField()
    outstanding_amount = serializers.DecimalField(
        max_digits=18, decimal_places=2, min_value=Decimal("0.01")
    )


class ObligationEdit(serializers.Serializer):
    description = serializers.CharField(max_length=200, required=False)
    counterparty = serializers.CharField(max_length=200, required=False, allow_blank=True)
    due_date = serializers.DateField(required=False)
    cancelled = serializers.BooleanField(required=False)


class SettlementInput(serializers.Serializer):
    transaction_id = serializers.IntegerField(min_value=1)
    amount = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=Decimal("0.01"))
    request_id = serializers.UUIDField()


class ObligationOutput(serializers.ModelSerializer):
    status = serializers.SerializerMethodField()

    def get_status(self, instance: Obligation) -> str:
        return (
            "cancelled"
            if instance.cancelled
            else "settled"
            if instance.outstanding_amount == 0
            else "pending"
        )

    class Meta:
        model = Obligation
        fields = [
            "id",
            "reference",
            "description",
            "counterparty",
            "direction",
            "due_date",
            "outstanding_amount",
            "cancelled",
            "status",
        ]
