from django.conf import settings
from django.db import models

from patients.models import Patient


class ClinicRequest(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT)
    actor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT)
    kind = models.CharField(
        max_length=16,
        choices=[("appointment", "Appointment"), ("clarification", "Clarification"), ("repeat", "Repeat medicine")],
    )
    channel = models.CharField(
        max_length=16, choices=[("portal", "Portal"), ("phone", "Phone"), ("in_person", "In person")], default="portal"
    )
    status = models.CharField(max_length=32, default="received")
    priority = models.PositiveSmallIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    idempotency_key = models.CharField(max_length=64)
    payload_digest = models.CharField(max_length=64)
    time_sensitive = models.BooleanField(default=False)
    reason = models.TextField(blank=True)
    message = models.TextField(blank=True)
    starts_at = models.DateTimeField(null=True, blank=True)
    ends_at = models.DateTimeField(null=True, blank=True)
    preference = models.CharField(
        max_length=16, choices=[("pickup", "Pickup"), ("delivery", "Delivery")], default="pickup"
    )
    delivery_address = models.CharField(max_length=300, blank=True)
    change_requested = models.BooleanField(default=False)
    change_version = models.PositiveIntegerField(default=0)
    change_starts_at = models.DateTimeField(null=True, blank=True)
    change_ends_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["actor", "idempotency_key"], name="actor_intake_idempotency")]
        ordering = ["-priority", "created_at"]
