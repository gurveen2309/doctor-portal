from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from intake.models import ClinicRequest
from patients.models import Patient


class Fulfillment(models.Model):
    request = models.OneToOneField(ClinicRequest, on_delete=models.PROTECT)
    status = models.CharField(max_length=16, default="approved")
    carrier = models.CharField(max_length=100, blank=True)
    tracking_number = models.CharField(max_length=100, blank=True)
    tracking_link = models.URLField(blank=True)
    cancellation_pending = models.BooleanField(default=False)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    updated_at = models.DateTimeField(auto_now=True)


class Charge(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT)
    category = models.CharField(
        max_length=16, choices=[("consultation", "Consultation"), ("medicine", "Medicine"), ("delivery", "Delivery")]
    )
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)


class ChargeCorrection(models.Model):
    charge = models.ForeignKey(Charge, on_delete=models.PROTECT, related_name="corrections")
    previous_amount = models.DecimalField(max_digits=10, decimal_places=2)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)


class ReceiptQuerySet(models.QuerySet["ReceiptEntry"]):
    def update(self, **kwargs: Any) -> int:
        raise ValidationError("Receipt history is immutable; use a correction.")

    def delete(self) -> tuple[int, dict[str, int]]:
        raise ValidationError("Receipt history is immutable; use a correction.")


class ReceiptEntry(models.Model):
    charge = models.ForeignKey(Charge, on_delete=models.PROTECT, related_name="receipts")
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    method = models.CharField(
        max_length=8, choices=[("cash", "Cash received externally"), ("upi", "UPI received externally")]
    )
    corrects = models.OneToOneField("self", on_delete=models.PROTECT, null=True, related_name="correction")
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    objects = ReceiptQuerySet.as_manager()

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self._state.adding:
            raise ValidationError("Receipt history is immutable; use a correction.")
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Receipt history is immutable; use a correction.")
