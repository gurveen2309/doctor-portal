from django.contrib.postgres.constraints import ExclusionConstraint
from django.contrib.postgres.fields import DateTimeRangeField, RangeOperators
from django.db import models

from intake.models import ClinicRequest
from patients.models import Patient


class Appointment(models.Model):
    request = models.ForeignKey(ClinicRequest, on_delete=models.PROTECT)
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT)
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    status = models.CharField(max_length=16, default="confirmed")

    class Meta:
        constraints = [
            models.CheckConstraint(condition=models.Q(ends_at__gt=models.F("starts_at")), name="appointment_order"),
            ExclusionConstraint(
                name="no_confirmed_calendar_overlap",
                expressions=[
                    (
                        models.Func(
                            "starts_at",
                            "ends_at",
                            models.Value("[)"),
                            function="TSTZRANGE",
                            output_field=DateTimeRangeField(),
                        ),
                        RangeOperators.OVERLAPS,
                    )
                ],
                condition=models.Q(status="confirmed"),
            ),
        ]


class AppointmentProposal(models.Model):
    request = models.ForeignKey(ClinicRequest, on_delete=models.PROTECT)
    original = models.ForeignKey(Appointment, on_delete=models.PROTECT, null=True, related_name="change_proposals")
    starts_at = models.DateTimeField()
    ends_at = models.DateTimeField()
    state = models.CharField(max_length=16, default="proposed")
    change_version = models.PositiveIntegerField(default=0)
    appointment = models.ForeignKey(Appointment, on_delete=models.PROTECT, null=True, related_name="accepted_proposals")
