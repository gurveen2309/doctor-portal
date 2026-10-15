import base64
import getpass
import secrets
from typing import Any

from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand, CommandError
from django.db import IntegrityError, transaction
from django_otp.plugins.otp_static.models import StaticDevice, StaticToken
from django_otp.plugins.otp_totp.models import TOTPDevice

from accounts.models import Account
from accounts.services import normalize_phone
from audit.services import record


class Command(BaseCommand):
    help = "Provision the first doctor locally with password, confirmed TOTP and offline one-time recovery codes."

    def handle(self, *args: Any, **options: Any) -> None:
        if Account.objects.filter(is_doctor=True).exists():
            raise CommandError(
                "A doctor already exists. Device replacement requires the controlled recovery procedure."
            )
        username = input("Doctor username: ").strip()
        phone = input("Doctor Indian mobile: ").strip()
        password = getpass.getpass("New doctor password: ")
        repeated = getpass.getpass("Repeat doctor password: ")
        if password != repeated:
            raise CommandError("Passwords do not match.")
        try:
            with transaction.atomic():
                account = Account(username=username, phone=normalize_phone(phone), is_doctor=True)
                account.full_clean(exclude=["password"])
                validate_password(password, account)
                account.set_password(password)
                account.save()
                device = TOTPDevice.objects.create(user=account, name="Doctor authenticator", confirmed=False)
                key = base64.b32encode(device.bin_key).decode()
                self.stdout.write("Sensitive setup: do not record, redirect, share or log this terminal output.")
                self.stdout.write(f"Enter this key in your local authenticator (SHA1, 6 digits, 30 seconds): {key}")
                token = getpass.getpass("Authenticator code: ")
                if not device.verify_token(token):
                    raise CommandError("Authenticator verification failed; provisioning rolled back.")
                device.confirmed = True
                device.save(update_fields=["confirmed"])
                backup = StaticDevice.objects.create(user=account, name="Offline recovery", confirmed=True)
                codes = [secrets.token_hex(8) for _ in range(8)]
                for code in codes:
                    StaticToken.objects.create(device=backup, token=code)
                record(account, "doctor.provisioned", account)
        except (ValidationError, IntegrityError) as error:
            raise CommandError(
                "Provisioning rejected; validate username/mobile/password and single-doctor ownership."
            ) from error
        self.stdout.write("Store these one-time recovery codes offline; each requires your password:")
        for code in codes:
            self.stdout.write(code)
        self.stdout.write("Doctor MFA provisioning completed. No patient access or production approval was granted.")
