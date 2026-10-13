from datetime import datetime

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.utils import timezone

from accounts.models import Account
from appointments.models import Appointment, AppointmentProposal
from audit.services import record
from clinic.models import AvailabilityWindow, Closure
from clinic.services import lock_calendar, validate_interval
from intake.models import ClinicRequest
from patients.permissions import require_access, require_doctor


def check_slot(starts_at: datetime, ends_at: datetime, original: Appointment | None = None) -> None:
    validate_interval(starts_at, ends_at)
    if starts_at <= timezone.now():
        raise ValidationError("Choose a future appointment.")
    if not AvailabilityWindow.objects.filter(starts_at__lte=starts_at, ends_at__gte=ends_at).exists():
        raise ValidationError("The requested time is not published as available.")
    if Closure.objects.filter(starts_at__lt=ends_at, ends_at__gt=starts_at).exists():
        raise ValidationError("The requested time is closed.")
    overlaps = Appointment.objects.filter(status="confirmed", starts_at__lt=ends_at, ends_at__gt=starts_at)
    if original:
        overlaps = overlaps.exclude(pk=original.pk)
    if overlaps.exists():
        raise ValidationError("This time is no longer available.")


@transaction.atomic
def confirm_requested(actor: Account, request: ClinicRequest) -> Appointment:
    require_doctor(actor)
    lock_calendar()
    row = ClinicRequest.objects.select_for_update().get(pk=request.pk)
    if row.kind != "appointment" or row.starts_at is None or row.ends_at is None:
        raise ValidationError("Only a requested appointment time can be directly confirmed.")
    existing = Appointment.objects.filter(request=row, status="confirmed").first()
    if existing:
        return existing
    if row.status != "received":
        raise ValidationError("Request is not awaiting confirmation.")
    check_slot(row.starts_at, row.ends_at)
    appointment = Appointment.objects.create(
        request=row, patient=row.patient, starts_at=row.starts_at, ends_at=row.ends_at
    )
    row.status = "confirmed"
    row.save(update_fields=["status"])
    record(actor, "appointment.confirmed", appointment)
    return appointment


@transaction.atomic
def propose_alternative(
    actor: Account,
    request: ClinicRequest,
    starts_at: datetime,
    ends_at: datetime,
    *,
    original: Appointment | None = None,
) -> AppointmentProposal:
    require_doctor(actor)
    validate_interval(starts_at, ends_at)
    lock_calendar()
    row = ClinicRequest.objects.select_for_update().get(pk=request.pk)
    if row.kind != "appointment" or row.status in {"cancelled", "completed"}:
        raise ValidationError("A live appointment request is required.")
    if original:
        original = Appointment.objects.select_for_update().get(pk=original.pk)
        if original.request_id != row.pk or original.status != "confirmed":
            raise ValidationError("Rescheduling requires this request's current booking.")
    elif Appointment.objects.filter(request=row, status="confirmed").exists():
        raise ValidationError("Use the confirmed original for rescheduling.")
    AppointmentProposal.objects.filter(request=row, state="proposed").update(state="superseded")
    proposal = AppointmentProposal.objects.create(
        request=row, starts_at=starts_at, ends_at=ends_at, original=original, change_version=row.change_version
    )
    if not original:
        row.status = "alternative_proposed"
        row.save(update_fields=["status"])
    record(actor, "appointment.proposed", proposal)
    return proposal


@transaction.atomic
def accept_proposal(actor: Account, proposal: AppointmentProposal) -> Appointment:
    require_access(actor, proposal.request.patient, "admin")
    if actor.is_doctor:
        raise PermissionDenied("An authorized patient account must explicitly accept the alternative.")
    lock_calendar()
    row = AppointmentProposal.objects.select_for_update().select_related("request").get(pk=proposal.pk)
    if row.state == "accepted" and row.appointment_id:
        accepted = Appointment.objects.get(pk=row.appointment_id)
        if accepted.status != "confirmed":
            raise ValidationError("The accepted booking is no longer confirmed.")
        return accepted
    if row.state != "proposed" or row.request.status == "cancelled":
        raise ValidationError("This proposal is no longer awaiting acceptance.")
    original = None
    if row.original_id:
        original = Appointment.objects.select_for_update().get(pk=row.original_id)
        if original.status != "confirmed":
            raise ValidationError("Original booking is no longer confirmed.")
    check_slot(row.starts_at, row.ends_at, original)
    if original:
        original.status = "rescheduled"
        original.save(update_fields=["status"])
    appointment = Appointment.objects.create(
        request=row.request, patient=row.request.patient, starts_at=row.starts_at, ends_at=row.ends_at
    )
    row.state, row.appointment = "accepted", appointment
    row.save(update_fields=["state", "appointment"])
    row.request.status = "confirmed"
    fields = ["status"]
    if row.request.change_requested and row.request.change_version == row.change_version:
        row.request.change_requested = False
        row.request.change_starts_at = row.request.change_ends_at = None
        fields.extend(["change_requested", "change_starts_at", "change_ends_at"])
    row.request.save(update_fields=fields)
    record(actor, "appointment.accepted", appointment)
    return appointment


@transaction.atomic
def cancel_request(actor: Account, request: ClinicRequest) -> None:
    require_access(actor, request.patient, "admin")
    lock_calendar()
    row = ClinicRequest.objects.select_for_update().get(pk=request.pk)
    if row.kind != "appointment" or row.status in {"cancelled", "completed"}:
        raise ValidationError("Only a live appointment request can be cancelled.")
    for appointment in Appointment.objects.select_for_update().filter(request=row, status="confirmed"):
        appointment.status = "cancelled"
        appointment.save(update_fields=["status"])
        record(actor, "appointment.cancelled", appointment)
    AppointmentProposal.objects.filter(request=row, state="proposed").update(state="superseded")
    row.status = "cancelled"
    row.change_requested = False
    row.change_starts_at = row.change_ends_at = None
    row.save(update_fields=["status", "change_requested", "change_starts_at", "change_ends_at"])
    record(actor, "request.cancelled", row)


@transaction.atomic
def cancel_appointment(actor: Account, appointment: Appointment) -> None:
    require_access(actor, appointment.patient, "admin")
    lock_calendar()
    row = Appointment.objects.select_for_update().get(pk=appointment.pk)
    if row.status != "confirmed":
        raise ValidationError("Only a confirmed appointment can be cancelled.")
    cancel_request(actor, row.request)


@transaction.atomic
def request_change(actor: Account, request: ClinicRequest, starts_at: datetime, ends_at: datetime) -> None:
    require_access(actor, request.patient, "admin")
    validate_interval(starts_at, ends_at)
    lock_calendar()
    row = ClinicRequest.objects.select_for_update().get(pk=request.pk)
    if row.kind != "appointment" or row.status in {"cancelled", "completed"}:
        raise ValidationError("Only a live appointment request can be changed.")
    row.change_requested, row.change_starts_at, row.change_ends_at = True, starts_at, ends_at
    row.change_version += 1
    row.save(update_fields=["change_requested", "change_version", "change_starts_at", "change_ends_at"])
    record(actor, "appointment.change_requested", row)
