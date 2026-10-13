from datetime import timedelta

import pytest
from django.test import Client
from django.utils import timezone

from tests.test_calendar import calendar_data
from tests.test_identity import identities

pytestmark = pytest.mark.django_db


def verified_client(doctor) -> Client:
    client = Client()
    client.force_login(doctor)
    session = client.session
    session["otp_device_id"] = doctor.otp_device.persistent_id
    session.save()
    return client


def test_public_portal_submission_and_doctor_workspace() -> None:
    doctor, patient, user = identities()
    from patients.models import AccessGrant

    AccessGrant.objects.create(account=user, patient=patient, admin=True, verified_by=doctor)
    client = Client()
    assert client.get("/").status_code == 200
    client.force_login(user)
    assert client.get("/portal/").status_code == 200
    response = client.post(
        f"/patients/{patient.pk}/request/",
        {"kind": "repeat", "idempotency_key": "ui-repeat", "preference": "pickup", "message": "PRIVATE-MESSAGE"},
    )
    assert response.status_code == 302
    page = client.get(response["Location"])
    assert b"Received" in page.content
    assert b"PRIVATE-MESSAGE" not in page.content
    assert verified_client(doctor).get("/doctor/").status_code == 200
    assert verified_client(doctor).get("/clinic/settings/").status_code == 200


def test_admin_only_detail_htmx_and_clinical_history_never_leak_text() -> None:
    doctor, patient, user, request, _, _ = calendar_data()
    from clinical.services import record_visit, revise_instructions
    from patients.models import AccessGrant

    visit = record_visit(doctor, patient)
    revise_instructions(doctor, visit, medicine="PRIVATE-MEDICINE", precautions="", diet="")
    AccessGrant.objects.filter(account=user).update(clinical=False)
    client = Client()
    client.force_login(user)
    for headers in ({}, {"HTTP_HX_REQUEST": "true"}):
        response = client.get(f"/requests/{request.pk}/", **headers)
        assert response.status_code == 200
        assert b"PRIVATE-CLINICAL" not in response.content
        assert client.get(f"/patients/{patient.pk}/history/", **headers).status_code == 404
    AccessGrant.objects.filter(account=user).update(revoked_at=timezone.now())
    assert client.get(f"/requests/{request.pk}/").status_code == 404


def test_patient_cannot_forge_doctor_actions_and_csrf_is_enforced() -> None:
    doctor, patient, user, request, _, _ = calendar_data()
    client = Client()
    client.force_login(user)
    assert client.post(f"/requests/{request.pk}/doctor/", {"action": "repeat", "outcome": "approve"}).status_code == 403
    assert client.get("/patients/manage/").status_code == 403
    assert client.get("/doctor/").status_code == 403
    csrf_client = Client(enforce_csrf_checks=True)
    csrf_client.force_login(user)
    assert (
        csrf_client.post(f"/patients/{patient.pk}/request/", {"kind": "repeat"}, HTTP_HX_REQUEST="true").status_code
        == 403
    )


def test_change_request_and_acceptance_preserve_then_replace_booking() -> None:
    doctor, patient, user, request, start, end = calendar_data()
    from appointments.services import confirm_requested, propose_alternative

    original = confirm_requested(doctor, request)
    client = Client()
    client.force_login(user)
    response = client.post(
        f"/requests/{request.pk}/change/",
        {"starts_at": end.isoformat(), "ends_at": (end + timedelta(minutes=30)).isoformat()},
    )
    assert response.status_code == 302
    original.refresh_from_db()
    assert original.status == "confirmed"
    proposal = propose_alternative(doctor, request, end, end + timedelta(minutes=30), original=original)
    assert client.post(f"/proposals/{proposal.pk}/accept/").status_code == 302
    original.refresh_from_db()
    assert original.status == "rescheduled"


def test_missing_information_submission_is_clinical_only() -> None:
    doctor, patient, user, _, _, _ = calendar_data()
    from clinical.services import reply_clarification
    from intake.services import submit_request
    from patients.models import AccessGrant

    request = submit_request(user, patient, "clarification", idempotency_key="ui-clarify")
    reply_clarification(doctor, request, "missing_information", "PRIVATE-REPLY")
    client = Client()
    client.force_login(user)
    assert client.post(f"/requests/{request.pk}/information/", {"message": "PRIVATE-ANSWER"}).status_code == 302
    AccessGrant.objects.filter(account=user).update(clinical=False)
    assert client.post(f"/requests/{request.pk}/information/", {"message": "Forged"}).status_code == 404
