import logging
from datetime import timedelta
from uuid import uuid4

import pytest
from django.contrib.auth.hashers import make_password
from django.test import Client, RequestFactory
from django.urls import reverse
from django.utils import timezone
from django.views.debug import get_exception_reporter_class

from tests.test_calendar import calendar_data

pytestmark = pytest.mark.django_db
SYNTHETIC_PHONE = "+919000000002"


def test_otp_database_failure_reports_no_submitted_code(settings, monkeypatch, caplog) -> None:
    from accounts.models import OTPChallenge

    settings.DEBUG = False
    settings.ADMINS = [("Synthetic operator", "operator@example.invalid")]
    secret = "831769"
    challenge = OTPChallenge.objects.create(
        phone="+919000000002", code_hash=make_password("864991"), expires_at=timezone.now() + timedelta(minutes=5)
    )

    def broken_save(self, *args, **kwargs):
        raise RuntimeError("Synthetic database failure")

    monkeypatch.setattr(OTPChallenge, "save", broken_save)
    client = Client(raise_request_exception=False)
    session = client.session
    session["patient_challenge"] = str(challenge.pk)
    session.save()
    response = client.post(reverse("verify-code"), {"code": secret})
    assert response.status_code == 500
    exc_type, exc_value, traceback = response.exc_info
    reporter = get_exception_reporter_class(response.wsgi_request)(
        response.wsgi_request, exc_type, exc_value, traceback, is_email=True
    )
    assert secret not in reporter.get_traceback_text()
    assert secret not in reporter.get_traceback_html()
    assert secret not in caplog.text
    from django.core import mail

    assert mail.outbox and secret not in mail.outbox[-1].body


def test_private_clinical_failure_redacts_post_locals_and_exception_value(settings, monkeypatch, caplog) -> None:
    from intake.models import ClinicRequest

    settings.DEBUG = False
    _, patient, user, _, _, _ = calendar_data()
    secret = "SYNTHETIC-PRIVATE-INSTRUCTION"

    def broken_save(self, *args, **kwargs):
        raise RuntimeError(self.message)

    monkeypatch.setattr(ClinicRequest, "save", broken_save)
    client = Client(raise_request_exception=False)
    client.force_login(user)
    response = client.post(
        f"/patients/{patient.pk}/request/",
        {"kind": "clarification", "message": secret, "preference": "pickup", "idempotency_key": "error-privacy"},
    )
    assert response.status_code == 500
    exc_type, exc_value, traceback = response.exc_info
    reporter = get_exception_reporter_class(response.wsgi_request)(
        response.wsgi_request, exc_type, exc_value, traceback, is_email=True
    )
    assert secret not in reporter.get_traceback_text()
    assert secret not in reporter.get_traceback_html()
    assert secret not in caplog.text


def test_unexpected_provider_failure_redacts_generated_code_and_phone(settings) -> None:
    from accounts.services import request_otp

    settings.DEBUG = False
    secrets: list[str] = []

    class BrokenDelivery:
        def deliver(self, phone: str, code: str) -> None:
            secrets.extend([phone, code])
            raise RuntimeError(f"Provider rejected {phone} / {code}")

    with pytest.raises(RuntimeError) as caught:
        request_otp(SYNTHETIC_PHONE, str(uuid4()), delivery=BrokenDelivery())
    request = RequestFactory().post("/accounts/login/", {"phone": secrets[0]})
    reporter = get_exception_reporter_class(request)(
        request, type(caught.value), caught.value, caught.value.__traceback__, is_email=True
    )
    for secret in secrets:
        assert secret not in reporter.get_traceback_text()
        assert secret not in reporter.get_traceback_html()


def test_application_error_logs_redact_values_without_hiding_failure(caplog) -> None:
    secret = "SYNTHETIC-SENSITIVE-ERROR"
    try:
        raise RuntimeError(secret)
    except RuntimeError:
        logging.getLogger("django.request").error("Request failed: %s", secret, exc_info=True)
    assert secret not in caplog.text
    assert "ERROR" in caplog.text
