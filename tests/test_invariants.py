from datetime import date, timedelta
from decimal import Decimal

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.test import Client
from django.utils import timezone

from tests.test_calendar import calendar_data
from tests.test_ui import verified_client

pytestmark = pytest.mark.django_db


def test_doctor_cannot_accept_own_alternative_without_patient_action() -> None:
    doctor, _, _, request, start, end = calendar_data()
    from appointments.services import accept_proposal, propose_alternative

    proposal = propose_alternative(doctor, request, start, end)
    with pytest.raises(PermissionDenied):
        accept_proposal(doctor, proposal)


def test_unconfirmed_cancellation_blocks_confirmation_and_acceptance() -> None:
    doctor, patient, user, request, start, end = calendar_data()
    from appointments.services import accept_proposal, confirm_requested, propose_alternative

    proposal = propose_alternative(doctor, request, start, end)
    client = Client()
    client.force_login(user)
    assert client.post(f"/requests/{request.pk}/cancel/").status_code == 302
    with pytest.raises(ValidationError):
        accept_proposal(user, proposal)
    with pytest.raises(ValidationError):
        confirm_requested(doctor, request)


def test_clinic_closure_and_window_removal_preserve_booked_appointments() -> None:
    doctor, _, _, request, start, end = calendar_data()
    from appointments.services import confirm_requested
    from clinic.models import AvailabilityWindow
    from clinic.services import publish_window

    original = confirm_requested(doctor, request)
    with pytest.raises(ValidationError):
        publish_window(doctor, start, end, closed=True)
    response = verified_client(doctor).post(
        "/clinic/settings/", {"action": "remove", "window": AvailabilityWindow.objects.first().pk}
    )
    assert response.status_code == 200
    original.refresh_from_db()
    assert original.status == "confirmed"
    assert AvailabilityWindow.objects.exists()


def test_clinical_only_grant_can_use_history_and_clarification_ui() -> None:
    doctor, patient, user, _, _, _ = calendar_data()
    from patients.models import AccessGrant

    AccessGrant.objects.filter(account=user).update(admin=False)
    client = Client()
    client.force_login(user)
    assert client.get(f"/patients/{patient.pk}/").status_code == 200
    response = client.post(
        f"/patients/{patient.pk}/request/",
        {"kind": "clarification", "message": "PRIVATE", "preference": "pickup", "idempotency_key": "clinical-only"},
    )
    assert response.status_code == 302
    assert client.get(response["Location"]).status_code == 200


def test_full_manual_doctor_flows_and_patient_status() -> None:
    doctor, patient, user, _, _, _ = calendar_data()
    from intake.services import submit_request

    repeat = submit_request(user, patient, "repeat", idempotency_key="full-ops")
    client = verified_client(doctor)
    assert client.post(f"/requests/{repeat.pk}/doctor/", {"action": "repeat", "outcome": "approve"}).status_code == 302
    assert (
        client.post(f"/requests/{repeat.pk}/doctor/", {"action": "fulfillment", "status": "preparing"}).status_code
        == 302
    )
    signed_in = Client()
    signed_in.force_login(user)
    response = signed_in.get(f"/requests/{repeat.pk}/")
    assert b"Preparing" in response.content
    assert (
        client.post(
            f"/patients/{patient.pk}/payments/", {"action": "charge", "category": "medicine", "amount": "250.00"}
        ).status_code
        == 302
    )


def test_charge_correction_preserves_prior_amount_and_actor() -> None:
    doctor, patient, _, _, _, _ = calendar_data()
    from operations.services import correct_charge, record_charge

    charge = record_charge(doctor, patient, "consultation", Decimal("100.00"))
    revision = correct_charge(doctor, charge, Decimal("150.00"))
    assert revision.previous_amount == Decimal("100.00") and revision.actor_id == doctor.pk
    charge.refresh_from_db()
    assert charge.amount == Decimal("150.00")


def test_restore_hold_invalidates_sessions_and_blocks_patient_access() -> None:
    doctor, patient, user, _, _, _ = calendar_data()
    from django.contrib.sessions.models import Session

    from accounts import services
    from patients.permissions import require_access

    client = Client()
    client.force_login(user)
    assert Session.objects.exists()
    assert hasattr(services, "hold_after_restore"), "Restore suspension is not implemented"
    services.hold_after_restore(doctor)
    assert not Session.objects.exists()
    with pytest.raises(PermissionDenied):
        require_access(user, patient, "admin")


def test_invalid_real_provider_configuration_reports_gate(monkeypatch) -> None:
    from config.checks import production_errors

    errors = production_errors(
        {
            "ENVIRONMENT": "production",
            "SECRET_KEY": "x" * 60,
            "DEBUG": False,
            "ALLOWED_HOSTS": ["clinic.example"],
            "SECURE_SSL_REDIRECT": True,
            "SESSION_COOKIE_SECURE": True,
            "CSRF_COOKIE_SECURE": True,
            "PATIENT_OTP_PROVIDER": "missing.provider.Adapter",
            "LIVE_DATA_APPROVED": True,
        }
    )
    assert any(error.id == "portal.E004" for error in errors)


@pytest.mark.parametrize("channel", ["phone", "in_person"])
def test_doctor_entered_channels_share_portal_overlap_and_adjacent_rules(channel: str) -> None:
    doctor, patient, _, request, start, end = calendar_data()
    from appointments.models import Appointment
    from appointments.services import confirm_requested
    from intake.services import submit_request

    confirm_requested(doctor, request)
    competing = submit_request(
        doctor, patient, "appointment", idempotency_key="competing", channel=channel, starts_at=start, ends_at=end
    )
    with pytest.raises(ValidationError):
        confirm_requested(doctor, competing)
    adjacent = submit_request(
        doctor,
        patient,
        "appointment",
        idempotency_key="adjacent",
        channel=channel,
        starts_at=end,
        ends_at=end + timedelta(minutes=30),
    )
    confirm_requested(doctor, adjacent)
    assert Appointment.objects.filter(status="confirmed").count() == 2


@pytest.mark.parametrize(("today", "allowed"), [(date(2026, 2, 27), True), (date(2026, 2, 28), False)])
def test_leap_day_guardian_access_stops_at_documented_conservative_cutoff(today, allowed, monkeypatch) -> None:
    doctor, patient, user, _, _, _ = calendar_data()
    from patients.models import AccessGrant
    from patients.permissions import require_access

    patient.date_of_birth = date(2008, 2, 29)
    patient.save()
    AccessGrant.objects.filter(account=user).update(relationship="guardian")
    monkeypatch.setattr("patients.permissions.timezone.localdate", lambda: today)
    if allowed:
        require_access(user, patient, "clinical")
    else:
        with pytest.raises(PermissionDenied):
            require_access(user, patient, "clinical")


def test_aged_repeat_never_becomes_approved_or_preparable() -> None:
    doctor, patient, user, _, _, _ = calendar_data()
    from clinical.models import RepeatDecision
    from intake.models import ClinicRequest
    from intake.services import submit_request
    from operations.models import Fulfillment
    from operations.services import advance_fulfillment

    row = submit_request(user, patient, "repeat", idempotency_key="aged-repeat")
    ClinicRequest.objects.filter(pk=row.pk).update(created_at=timezone.now() - timedelta(days=45))
    with pytest.raises(ValidationError):
        advance_fulfillment(doctor, row, "preparing")
    row.refresh_from_db()
    assert row.status == "received"
    assert not RepeatDecision.objects.filter(request=row).exists()
    assert not Fulfillment.objects.filter(request=row).exists()


def test_repeat_decline_records_actor_without_authorizing_fulfillment() -> None:
    doctor, patient, user, _, _, _ = calendar_data()
    from clinical.services import decide_repeat
    from intake.services import submit_request
    from operations.services import advance_fulfillment

    row = submit_request(user, patient, "repeat", idempotency_key="declined-repeat")
    decision = decide_repeat(doctor, row, "decline")
    assert decision.actor_id == doctor.pk and decision.decided_at is not None
    with pytest.raises(ValidationError):
        advance_fulfillment(doctor, row, "preparing")
