import pytest
from django.test import Client

from tests.test_calendar import calendar_data
from tests.test_ui import verified_client

pytestmark = pytest.mark.django_db


def test_htmx_priority_uses_same_doctor_mfa_and_csrf_rules() -> None:
    doctor, _, user, row, _, _ = calendar_data()
    client = verified_client(doctor)
    response = client.post(f"/requests/{row.pk}/priority/", {"priority": 2}, HTTP_HX_REQUEST="true")
    assert response.status_code == 200
    row.refresh_from_db()
    assert row.priority == 2
    assert b"priority-control" in response.content and b"<html" not in response.content
    patient = Client()
    patient.force_login(user)
    assert patient.post(f"/requests/{row.pk}/priority/", {"priority": 0}, HTTP_HX_REQUEST="true").status_code == 403
    csrf = Client(enforce_csrf_checks=True)
    csrf.force_login(doctor)
    assert csrf.post(f"/requests/{row.pk}/priority/", {"priority": 0}, HTTP_HX_REQUEST="true").status_code == 403
