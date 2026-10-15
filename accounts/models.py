import uuid

from django.contrib.auth.models import AbstractUser
from django.db import models


class Account(AbstractUser):
    phone = models.CharField(max_length=16, unique=True)
    is_doctor = models.BooleanField(default=False)
    phone_control = models.CharField(
        max_length=16,
        choices=[("unreviewed", "Unreviewed"), ("shared", "Shared"), ("private", "Personally controlled")],
        default="unreviewed",
    )
    phone_reviewed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        verbose_name = "user"
        verbose_name_plural = "users"
        abstract = False
        constraints = [
            models.UniqueConstraint(fields=["is_doctor"], condition=models.Q(is_doctor=True), name="one_clinic_doctor")
        ]

    def is_verified(self) -> bool:
        device = getattr(self, "otp_device", None)
        return bool(device and device.confirmed and device.user_id == self.pk)


class OTPChallenge(models.Model):
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    phone = models.CharField(max_length=16, db_index=True)
    code_hash = models.CharField(max_length=128)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    attempts = models.PositiveSmallIntegerField(default=0)
    consumed_at = models.DateTimeField(null=True)


class AuthThrottle(models.Model):
    key = models.CharField(max_length=64, primary_key=True)
    window_start = models.DateTimeField()
    count = models.PositiveIntegerField(default=0)


class AccessControl(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    patient_access_suspended = models.BooleanField(default=False)
