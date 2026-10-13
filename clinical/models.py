from typing import Any

from django.conf import settings
from django.core.exceptions import ValidationError
from django.db import models

from intake.models import ClinicRequest
from patients.models import Patient


class Visit(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    follow_up_date = models.DateField(null=True, blank=True)


class RevisionQuerySet(models.QuerySet["InstructionRevision"]):
    def update(self, **kwargs: Any) -> int:
        raise ValidationError("Instruction revisions are immutable.")

    def delete(self) -> tuple[int, dict[str, int]]:
        raise ValidationError("Instruction revisions are immutable.")


class InstructionRevision(models.Model):
    visit = models.ForeignKey(Visit, on_delete=models.PROTECT, related_name="revisions")
    revision = models.PositiveIntegerField()
    medicine = models.TextField(blank=True)
    precautions = models.TextField(blank=True)
    diet = models.TextField(blank=True)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)
    objects = RevisionQuerySet.as_manager()

    class Meta:
        constraints = [models.UniqueConstraint(fields=["visit", "revision"], name="unique_visit_revision")]
        ordering = ["-revision"]

    def save(self, *args: Any, **kwargs: Any) -> None:
        if not self._state.adding:
            raise ValidationError("Instruction revisions are immutable.")
        super().save(*args, **kwargs)

    def delete(self, *args: Any, **kwargs: Any) -> tuple[int, dict[str, int]]:
        raise ValidationError("Instruction revisions are immutable.")


class ClarificationResponse(models.Model):
    request = models.ForeignKey(ClinicRequest, on_delete=models.PROTECT, related_name="responses")
    outcome = models.CharField(max_length=32)
    message = models.TextField()
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    created_at = models.DateTimeField(auto_now_add=True)


class RepeatDecision(models.Model):
    request = models.OneToOneField(ClinicRequest, on_delete=models.PROTECT, related_name="repeat_decision")
    outcome = models.CharField(
        max_length=32,
        choices=[("approve", "Approve"), ("decline", "Decline"), ("consultation_required", "Consultation required")],
    )
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    decided_at = models.DateTimeField(auto_now_add=True)
