from django.db import models


class ClinicProfile(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)
    name = models.CharField(max_length=100, blank=True)
    address = models.CharField(max_length=300, blank=True)
    map_link = models.URLField(blank=True)
    contact = models.CharField(max_length=100, blank=True)
    doctor_name = models.CharField(max_length=100, blank=True)
    opening_hours = models.CharField(max_length=200, blank=True)


class Calendar(models.Model):
    id = models.PositiveSmallIntegerField(primary_key=True, default=1, editable=False)


class AvailabilityWindow(models.Model):
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(ends_at__gt=models.F("starts_at")), name="window_order")
        ]


class Closure(models.Model):
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(ends_at__gt=models.F("starts_at")), name="closure_order")
        ]
