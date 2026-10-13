from io import StringIO

import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from django_otp.oath import totp

pytestmark = pytest.mark.django_db


def test_controlled_doctor_provisioning_requires_confirmed_authenticator(monkeypatch) -> None:
    from django_otp.plugins.otp_totp.models import TOTPDevice

    from accounts.models import Account

    answers = iter(["localdoctor", "+919000000003"])
    monkeypatch.setattr("builtins.input", lambda prompt: next(answers))

    def credential(prompt):
        if "Authenticator" in prompt:
            device = TOTPDevice.objects.get(user__username="localdoctor")
            return str(totp(device.bin_key, step=device.step, t0=device.t0))
        return "Synthetic-setup-password-123"

    monkeypatch.setattr("getpass.getpass", credential)
    try:
        call_command("setup_doctor", stdout=StringIO())
    except CommandError as error:
        pytest.fail(f"Controlled setup is not implemented: {error}")
    doctor = Account.objects.get(username="localdoctor")
    assert doctor.is_doctor and doctor.check_password("Synthetic-setup-password-123")
    assert TOTPDevice.objects.get(user=doctor).confirmed
    with pytest.raises(CommandError):
        call_command("setup_doctor", stdout=StringIO())
