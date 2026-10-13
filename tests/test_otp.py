import importlib.util
from datetime import timedelta

import pytest
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.test import override_settings
from django.utils import timezone

pytestmark = pytest.mark.django_db


class MemoryDelivery:
    def __init__(self) -> None:
        self.codes: list[tuple[str, str]] = []

    def deliver(self, phone: str, code: str) -> None:
        self.codes.append((phone, code))


def services():
    assert importlib.util.find_spec("accounts") is not None, "OTP service is not implemented"
    from accounts import services

    return services


def test_provider_missing_fails_closed() -> None:
    with override_settings(PATIENT_OTP_PROVIDER=""):
        with pytest.raises(ImproperlyConfigured):
            services().request_otp("+919000000002", "127.0.0.1")


def test_otp_consumption_resend_expiry_attempt_bounds_and_no_logging(caplog, monkeypatch) -> None:
    svc = services()
    from accounts.models import OTPChallenge

    delivery = MemoryDelivery()
    challenge = svc.request_otp("+919000000002", "127.0.0.1", delivery=delivery)
    code = delivery.codes[0][1]
    assert challenge.code_hash != code
    assert code not in caplog.text
    with pytest.raises(ValidationError, match="wait"):
        svc.request_otp("+919000000002", "127.0.0.1", delivery=delivery)
    for _ in range(5):
        with pytest.raises(ValidationError):
            svc.verify_otp(challenge.pk, "invalid")
    challenge.refresh_from_db()
    assert challenge.attempts == 5
    with pytest.raises(ValidationError):
        svc.verify_otp(challenge.pk, code)
    later = timezone.now() + timedelta(minutes=10)
    monkeypatch.setattr(timezone, "now", lambda: later)
    next_challenge = svc.request_otp("+919000000002", "127.0.0.1", delivery=delivery)
    user = svc.verify_otp(next_challenge.pk, delivery.codes[-1][1])
    assert user.phone == "+919000000002"
    with pytest.raises(ValidationError):
        svc.verify_otp(next_challenge.pk, delivery.codes[-1][1])
    later += timedelta(minutes=10)
    expired = svc.request_otp("+919000000002", "127.0.0.1", delivery=delivery)
    OTPChallenge.objects.filter(pk=expired.pk).update(expires_at=timezone.now() - timedelta(seconds=1))
    with pytest.raises(ValidationError):
        svc.verify_otp(expired.pk, delivery.codes[-1][1])
