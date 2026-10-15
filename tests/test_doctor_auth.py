import pytest
from django.test import Client
from django_otp.oath import totp
from django_otp.plugins.otp_static.models import StaticDevice, StaticToken

from tests.test_identity import identities

pytestmark = pytest.mark.django_db


def test_doctor_login_requires_password_and_real_mfa_verification() -> None:
    doctor, _, _ = identities()
    doctor.set_password("Synthetic-password-123")
    doctor.save()
    client = Client()
    response = client.post("/accounts/doctor-login/", {"username": "doctor", "password": "Synthetic-password-123"})
    assert response.status_code == 200
    assert "_auth_user_id" not in client.session
    token = totp(doctor.otp_device.bin_key, step=doctor.otp_device.step, t0=doctor.otp_device.t0)
    response = client.post(
        "/accounts/doctor-login/",
        {"username": "doctor", "password": "Synthetic-password-123", "token": str(token)},
    )
    assert response.status_code == 302
    assert client.session["otp_device_id"] == doctor.otp_device.persistent_id


def test_static_recovery_is_one_use_and_audited() -> None:
    doctor, _, _ = identities()
    doctor.set_password("Synthetic-password-123")
    doctor.save()
    device = StaticDevice.objects.create(user=doctor, confirmed=True)
    StaticToken.objects.create(device=device, token="synthetic-backup")
    response = Client().post(
        "/accounts/doctor-login/",
        {"username": "doctor", "password": "Synthetic-password-123", "token": "synthetic-backup", "recovery": "on"},
    )
    assert response.status_code == 302
    from audit.models import AuditEvent

    assert AuditEvent.objects.filter(action="doctor.recovery_used").exists()
    assert not device.token_set.exists()


def test_authentication_mutations_require_csrf() -> None:
    client = Client(enforce_csrf_checks=True)
    assert client.post("/accounts/doctor-login/", {}).status_code == 403
    assert client.post("/accounts/login/", {}).status_code == 403
