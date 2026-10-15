from django.conf import settings
from django.db import models


class Patient(models.Model):
    card_number = models.CharField(max_length=40, unique=True)
    name = models.CharField(max_length=100)
    date_of_birth = models.DateField(null=True, blank=True)
    verified_by = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)


class AccessGrant(models.Model):
    account = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="patient_grants")
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name="grants")
    admin = models.BooleanField(default=False)
    clinical = models.BooleanField(default=False)
    relationship = models.CharField(
        max_length=16,
        choices=[("self", "Self"), ("delegate", "Administrative delegate"), ("guardian", "Guardian")],
        default="self",
    )
    verified_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, related_name="verified_grants"
    )
    verified_at = models.DateTimeField(null=True)
    revoked_at = models.DateTimeField(null=True)

    class Meta:
        constraints = [models.UniqueConstraint(fields=["account", "patient"], name="unique_account_patient_grant")]
