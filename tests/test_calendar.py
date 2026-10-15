import importlib.util
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

import pytest
from django.core.exceptions import ValidationError
from django.db import IntegrityError, close_old_connections, connection, transaction
from django.utils import timezone

from tests.test_identity import identities


def calendar_data():
    assert importlib.util.find_spec("appointments") is not None, "Calendar is not implemented"
    from clinic.models import AvailabilityWindow, Calendar
    from intake.services import submit_request
    from patients.models import AccessGrant

    doctor, patient, user = identities()
    AccessGrant.objects.create(account=user, patient=patient, admin=True, clinical=True, verified_by=doctor)
    start = timezone.now() + timedelta(days=1)
    end = start + timedelta(minutes=30)
    Calendar.objects.create(pk=1)
    AvailabilityWindow.objects.create(starts_at=start, ends_at=start + timedelta(hours=4))
    request = submit_request(
        user, patient, "appointment", idempotency_key="first", starts_at=start, ends_at=end, message="PRIVATE-CLINICAL"
    )
    return doctor, patient, user, request, start, end


@pytest.mark.django_db
def test_duplicate_intake_and_time_sensitive_validation() -> None:
    doctor, patient, user, request, start, end = calendar_data()
    from intake.services import submit_request

    repeated = submit_request(
        user, patient, "appointment", idempotency_key="first", starts_at=start, ends_at=end, message="PRIVATE-CLINICAL"
    )
    assert repeated.pk == request.pk
    assert request.status == "received"
    with pytest.raises(ValidationError):
        submit_request(user, patient, "repeat", idempotency_key="first")
    with pytest.raises(ValidationError):
        submit_request(user, patient, "repeat", idempotency_key="second", time_sensitive=True)


@pytest.mark.django_db
def test_unreserved_alternatives_and_failed_reschedule_preserve_original() -> None:
    doctor, patient, user, request, start, end = calendar_data()
    from appointments.models import Appointment
    from appointments.services import accept_proposal, confirm_requested, propose_alternative
    from intake.services import submit_request

    original = confirm_requested(doctor, request)
    target_start, target_end = end, end + timedelta(minutes=30)
    proposal = propose_alternative(doctor, request, target_start, target_end, original=original)
    assert Appointment.objects.filter(status="confirmed").count() == 1
    competing = submit_request(
        doctor,
        patient,
        "appointment",
        idempotency_key="phone",
        channel="phone",
        starts_at=target_start,
        ends_at=target_end,
    )
    confirm_requested(doctor, competing)
    with pytest.raises(ValidationError):
        accept_proposal(user, proposal)
    original.refresh_from_db()
    assert original.status == "confirmed" and original.starts_at == start


@pytest.mark.django_db
def test_acceptance_rechecks_availability_and_replay() -> None:
    doctor, patient, user, request, start, end = calendar_data()
    from appointments.services import accept_proposal, propose_alternative
    from clinic.models import Closure

    proposal = propose_alternative(doctor, request, start, end)
    closure = Closure.objects.create(starts_at=start, ends_at=end)
    with pytest.raises(ValidationError):
        accept_proposal(user, proposal)
    closure.delete()
    appointment = accept_proposal(user, proposal)
    assert accept_proposal(user, proposal).pk == appointment.pk


@pytest.mark.django_db(transaction=True)
def test_mixed_channel_competing_confirmations_and_database_constraint() -> None:
    doctor, patient, user, request, start, end = calendar_data()
    assert connection.vendor == "postgresql"
    from django_otp.plugins.otp_totp.models import TOTPDevice

    from accounts.models import Account
    from appointments.models import Appointment
    from appointments.services import accept_proposal, confirm_requested, propose_alternative
    from intake.models import ClinicRequest
    from intake.services import submit_request

    proposal = propose_alternative(doctor, request, start, end)
    phone = submit_request(
        doctor, patient, "appointment", idempotency_key="phone", channel="phone", starts_at=start, ends_at=end
    )
    barrier = Barrier(2)

    def contender(channel: str) -> str:
        close_old_connections()
        try:
            actor = Account.objects.get(pk=doctor.pk if channel == "phone" else user.pk)
            if channel == "phone":
                actor.otp_device = TOTPDevice.objects.get(pk=doctor.otp_device.pk)
            barrier.wait(timeout=10)
            try:
                if channel == "phone":
                    confirm_requested(actor, ClinicRequest.objects.get(pk=phone.pk))
                else:
                    accept_proposal(actor, proposal)
            except ValidationError:
                return "rejected"
            return "confirmed"
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        outcomes = list(pool.map(contender, ["phone", "portal"]))
    assert sorted(outcomes) == ["confirmed", "rejected"]
    assert Appointment.objects.filter(status="confirmed").count() == 1
    with pytest.raises(IntegrityError), transaction.atomic():
        Appointment.objects.create(request=phone, patient=patient, starts_at=start, ends_at=end, status="confirmed")
