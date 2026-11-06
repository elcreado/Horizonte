"""Manual monthly commitments, materialized once per schedule and due date."""

import calendar
from datetime import date, timedelta
from decimal import Decimal

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import serializers
from rest_framework.decorators import api_view
from rest_framework.response import Response

from apps.accounts.models import AuditLog, Company

from .models import MonthlyOccurrence, MonthlySchedule, Obligation
from .obligations import membership


class ScheduleInput(serializers.Serializer):
    request_id = serializers.UUIDField()
    description = serializers.CharField(max_length=200)
    direction = serializers.ChoiceField(choices=["in", "out"], default="out")
    amount = serializers.DecimalField(max_digits=18, decimal_places=2, min_value=Decimal("0.01"))
    day = serializers.IntegerField(min_value=1, max_value=31)
    start_date = serializers.DateField(default=timezone.localdate)
    end_date = serializers.DateField(required=False, allow_null=True)

    def validate(self, values):
        if values.get("end_date") and values["end_date"] < values["start_date"]:
            raise serializers.ValidationError("La fecha final debe ser posterior al inicio.")
        return values


def schedule_data(row):
    return {
        "id": row.pk,
        "description": row.description,
        "direction": row.direction,
        "amount": str(row.amount),
        "day": row.day,
        "start_date": row.start_date.isoformat(),
        "end_date": row.end_date.isoformat() if row.end_date else None,
        "active": row.active,
    }


def materialize_monthly(company_id: int, through: date) -> None:
    """Expand active schedules up to the requested horizon; never recreate a paid/cancelled occurrence."""
    through = min(through, timezone.localdate() + timedelta(days=730))
    with transaction.atomic():
        Company.objects.select_for_update().get(pk=company_id)
        for schedule in MonthlySchedule.objects.filter(company_id=company_id, active=True):
            end = min(through, schedule.end_date) if schedule.end_date else through
            first = schedule.start_date
            last = (
                MonthlyOccurrence.objects.filter(schedule=schedule)
                .order_by("-date")
                .values_list("date", flat=True)
                .first()
            )
            month = (
                date(last.year + (last.month == 12), last.month % 12 + 1, 1)
                if last
                else first.replace(day=1)
            )
            while month <= end:
                due = date(
                    month.year,
                    month.month,
                    min(schedule.day, calendar.monthrange(month.year, month.month)[1]),
                )
                if schedule.start_date <= due <= end and due >= first:
                    if not MonthlyOccurrence.objects.filter(schedule=schedule, date=due).exists():
                        obligation = Obligation.objects.create(
                            company_id=company_id,
                            reference=f"monthly:{schedule.pk}:{due.isoformat()}",
                            description=schedule.description,
                            direction=schedule.direction,
                            due_date=due,
                            outstanding_amount=schedule.amount,
                        )
                        MonthlyOccurrence.objects.create(
                            schedule=schedule, date=due, obligation=obligation
                        )
                month = date(month.year + (month.month == 12), month.month % 12 + 1, 1)


@api_view(["GET", "POST"])
def monthly_schedules(request, company_id):
    if request.method == "GET":
        member = membership(request, company_id)
        return Response(
            {
                "can_edit": member.role in ("owner", "accountant"),
                "results": [
                    schedule_data(row)
                    for row in MonthlySchedule.objects.filter(company_id=company_id).order_by("-id")
                ],
            }
        )
    with transaction.atomic():
        membership(request, company_id, write=True)
        Company.objects.select_for_update().get(pk=company_id)
        serializer = ScheduleInput(data=request.data)
        serializer.is_valid(raise_exception=True)
        values = serializer.validated_data
        existing = MonthlySchedule.objects.filter(
            company_id=company_id, request_id=values["request_id"]
        ).first()
        if existing:
            if any(getattr(existing, key) != value for key, value in values.items()):
                return Response({"detail": "La solicitud ya se usó con otros datos."}, status=409)
            return Response(schedule_data(existing))
        row = MonthlySchedule.objects.create(company_id=company_id, user=request.user, **values)
        AuditLog.objects.create(
            company_id=company_id,
            user=request.user,
            action="monthly.created",
            entity="MonthlySchedule",
            entity_id=str(row.pk),
            after=schedule_data(row),
        )
        materialize_monthly(company_id, timezone.localdate() + timedelta(days=366))
    return Response(schedule_data(row), status=201)


@api_view(["POST"])
def cancel_monthly(request, company_id, schedule_id):
    with transaction.atomic():
        membership(request, company_id, write=True)
        Company.objects.select_for_update().get(pk=company_id)
        row = get_object_or_404(
            MonthlySchedule.objects.select_for_update(), pk=schedule_id, company_id=company_id
        )
        if row.active:
            before = schedule_data(row)
            row.active = False
            row.save(update_fields=["active"])
            Obligation.objects.filter(
                monthlyoccurrence__schedule=row,
                due_date__gte=timezone.localdate(),
                settlements__isnull=True,
            ).update(cancelled=True)
            AuditLog.objects.create(
                company_id=company_id,
                user=request.user,
                action="monthly.cancelled",
                entity="MonthlySchedule",
                entity_id=str(row.pk),
                before=before,
                after=schedule_data(row),
            )
    return Response(schedule_data(row))
