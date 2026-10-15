from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

import pytest
from django.core.exceptions import ValidationError
from django.db import close_old_connections, connection
from django.test import Client

from tests.test_calendar import calendar_data
from tests.test_ui import verified_client

pytestmark = pytest.mark.django_db


def test_request_cancellation_rechecks_current_calendar_occupancy() -> None:
    doctor, _, user, request, start, end = calendar_data()
    from appointments.services import confirm_requested, propose_alternative
    from operations.services import request_cancellation

    original = confirm_requested(doctor, request)
    proposal = propose_alternative(doctor, request, end, end + timedelta(minutes=30), original=original)
    request_cancellation(user, request)
    original.refresh_from_db()
    proposal.refresh_from_db()
    request.refresh_from_db()
    assert request.status == "cancelled"
    assert original.status == "cancelled"
    assert proposal.state == "superseded"


@pytest.mark.django_db(transaction=True)
def test_concurrent_confirmation_and_request_cancellation_leave_no_live_booking() -> None:
    doctor, _, user, request, _, _ = calendar_data()
    from django_otp.plugins.otp_totp.models import TOTPDevice

    from accounts.models import Account
    from appointments.models import Appointment
    from appointments.services import confirm_requested
    from intake.models import ClinicRequest
    from operations.services import request_cancellation

    assert connection.vendor == "postgresql"
    barrier = Barrier(2)

    def contender(action: str) -> None:
        close_old_connections()
        try:
            actor = Account.objects.get(pk=doctor.pk if action == "confirm" else user.pk)
            row = ClinicRequest.objects.get(pk=request.pk)
            if action == "confirm":
                actor.otp_device = TOTPDevice.objects.get(pk=doctor.otp_device.pk)
            barrier.wait(timeout=10)
            if action == "cancel":
                request_cancellation(actor, row)
            else:
                try:
                    confirm_requested(actor, row)
                except ValidationError:
                    pass
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        list(pool.map(contender, ["confirm", "cancel"]))
    request.refresh_from_db()
    assert request.status == "cancelled"
    assert not Appointment.objects.filter(request=request, status="confirmed").exists()


def test_clinical_only_account_can_cancel_its_clarification() -> None:
    _, patient, user, _, _, _ = calendar_data()
    from intake.services import submit_request
    from patients.models import AccessGrant

    AccessGrant.objects.filter(account=user).update(admin=False)
    row = submit_request(user, patient, "clarification", idempotency_key="cancel-clinical")
    client = Client()
    client.force_login(user)
    assert client.post(f"/requests/{row.pk}/cancel/").status_code == 302
    row.refresh_from_db()
    assert row.status == "cancelled"


def test_accepted_reschedule_resolves_only_the_proposed_change() -> None:
    doctor, _, user, request, _, end = calendar_data()
    from appointments.services import accept_proposal, confirm_requested, propose_alternative, request_change

    original = confirm_requested(doctor, request)
    request_change(user, request, end, end + timedelta(minutes=30))
    proposal = propose_alternative(doctor, request, end, end + timedelta(minutes=30), original=original)
    accept_proposal(user, proposal)
    request.refresh_from_db()
    assert not request.change_requested
    assert request.change_starts_at is None and request.change_ends_at is None
    assert b"Original booking remains" not in verified_client(doctor).get(f"/requests/{request.pk}/doctor/").content


def test_accepting_older_proposal_preserves_a_newer_change_request() -> None:
    doctor, _, user, request, _, end = calendar_data()
    from appointments.services import accept_proposal, confirm_requested, propose_alternative, request_change

    original = confirm_requested(doctor, request)
    request_change(user, request, end, end + timedelta(minutes=30))
    proposal = propose_alternative(doctor, request, end, end + timedelta(minutes=30), original=original)
    newer = end + timedelta(hours=1)
    request_change(user, request, newer, newer + timedelta(minutes=30))
    accept_proposal(user, proposal)
    request.refresh_from_db()
    assert request.change_requested and request.change_starts_at == newer


def test_actionable_queue_is_not_crowded_out_by_terminal_history() -> None:
    doctor, patient, _, pending, _, _ = calendar_data()
    from intake.models import ClinicRequest
    from operations.models import Fulfillment

    historical = [
        ClinicRequest(
            actor=doctor,
            patient=patient,
            kind="repeat",
            status="decline",
            priority=2,
            idempotency_key=f"history-{index}",
            payload_digest="synthetic",
        )
        for index in range(51)
    ]
    ClinicRequest.objects.bulk_create(historical)
    review = ClinicRequest.objects.create(
        actor=doctor,
        patient=patient,
        kind="repeat",
        status="fulfilled",
        idempotency_key="physical-review",
        payload_digest="synthetic",
    )
    Fulfillment.objects.create(request=review, actor=doctor, status="delivered", cancellation_pending=True)
    client = verified_client(doctor)
    page = client.get("/doctor/").context["page"]
    assert {row.pk for row in page} == {pending.pk, review.pk}
    history = client.get("/doctor/?view=history").context["page"]
    assert any(row.status == "decline" for row in history)


@pytest.mark.parametrize("htmx", [False, True])
def test_unavailable_patient_objects_have_consistent_not_found_responses(htmx: bool) -> None:
    doctor, _, user, _, start, end = calendar_data()
    from appointments.services import propose_alternative
    from intake.services import submit_request
    from patients.models import Patient

    hidden = Patient.objects.create(card_number="UNAVAILABLE", name="Synthetic unavailable", verified_by=doctor)
    row = submit_request(doctor, hidden, "appointment", idempotency_key="unavailable", starts_at=start, ends_at=end)
    proposal = propose_alternative(doctor, row, start, end)
    paths = [
        ("get", "/patients/{}/", hidden.pk),
        ("get", "/patients/{}/request/", hidden.pk),
        ("get", "/patients/{}/history/", hidden.pk),
        ("get", "/patients/{}/payments/", hidden.pk),
        ("get", "/requests/{}/", row.pk),
        ("post", "/requests/{}/change/", row.pk),
        ("post", "/requests/{}/cancel/", row.pk),
        ("post", "/requests/{}/information/", row.pk),
        ("post", "/proposals/{}/accept/", proposal.pk),
    ]
    client = Client()
    client.force_login(user)
    headers = {"HTTP_HX_REQUEST": "true"} if htmx else {}
    for method, pattern, identifier in paths:
        action = getattr(client, method)
        assert action(pattern.format(identifier), **headers).status_code == 404
        assert action(pattern.format(identifier + 1_000_000), **headers).status_code == 404


def test_duplicate_submission_reports_current_terminal_state() -> None:
    _, patient, user, _, _, _ = calendar_data()
    from intake.models import ClinicRequest
    from operations.services import request_cancellation

    client = Client()
    client.force_login(user)
    payload = {"kind": "repeat", "preference": "pickup", "idempotency_key": "replayed-state"}
    assert client.post(f"/patients/{patient.pk}/request/", payload, follow=True).status_code == 200
    row = ClinicRequest.objects.get(idempotency_key="replayed-state")
    request_cancellation(user, row)
    response = client.post(f"/patients/{patient.pk}/request/", payload, follow=True)
    assert response.status_code == 200
    assert b"Cancelled" in response.content
    assert b"awaiting review" not in response.content
    assert ClinicRequest.objects.filter(idempotency_key="replayed-state").count() == 1
