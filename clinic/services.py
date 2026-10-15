from datetime import datetime

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from accounts.models import Account
from audit.services import record
from clinic.models import AvailabilityWindow, Calendar, Closure
from patients.permissions import require_doctor


def lock_calendar() -> Calendar:
    Calendar.objects.get_or_create(pk=1)
    return Calendar.objects.select_for_update().get(pk=1)


def validate_interval(starts_at: datetime, ends_at: datetime) -> None:
    if timezone.is_naive(starts_at) or timezone.is_naive(ends_at) or ends_at <= starts_at:
        raise ValidationError("Provide aware start/end times with end after start.")


@transaction.atomic
def publish_window(actor: Account, starts_at: datetime, ends_at: datetime, *, closed: bool = False) -> int:
    require_doctor(actor)
    validate_interval(starts_at, ends_at)
    lock_calendar()
    from appointments.models import Appointment

    if closed and Appointment.objects.filter(status="confirmed", starts_at__lt=ends_at, ends_at__gt=starts_at).exists():
        raise ValidationError("Closure conflicts with confirmed bookings; resolve those explicitly first.")
    model = Closure if closed else AvailabilityWindow
    window = model.objects.create(starts_at=starts_at, ends_at=ends_at)
    record(actor, "calendar.closed" if closed else "calendar.published", window)
    return window.pk
