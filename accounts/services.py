import hashlib
import re
import secrets
from datetime import timedelta
from uuid import UUID

from django.conf import settings
from django.contrib.auth.hashers import check_password, make_password
from django.core.exceptions import ImproperlyConfigured, ValidationError
from django.db import transaction
from django.utils import timezone

from accounts.models import Account, AuthThrottle, OTPChallenge
from accounts.providers import Delivery, provider_from_path


def normalize_phone(phone: str) -> str:
    compact = re.sub(r"[\s()-]", "", phone)
    if re.fullmatch(r"[6-9]\d{9}", compact):
        compact = "+91" + compact
    if not re.fullmatch(r"\+91[6-9]\d{9}", compact):
        raise ValidationError("Enter a valid Indian mobile number.")
    return compact


def configured_delivery() -> Delivery:
    path: str = getattr(settings, "PATIENT_OTP_PROVIDER")
    return provider_from_path(path)


def throttle(key: str, *, limit: int, seconds: int) -> None:
    now = timezone.now()
    digest = hashlib.sha256(key.encode()).hexdigest()
    with transaction.atomic():
        AuthThrottle.objects.get_or_create(key=digest, defaults={"window_start": now})
        row = AuthThrottle.objects.select_for_update().get(pk=digest)
        if row.window_start + timedelta(seconds=seconds) <= now:
            row.window_start, row.count = now, 0
        if row.count >= limit:
            raise ValidationError("Too many attempts; wait before trying again.")
        row.count += 1
        row.save()


def request_otp(phone: str, source: str, *, delivery: Delivery | None = None) -> OTPChallenge:
    phone = normalize_phone(phone)
    if delivery is not None and getattr(settings, "ENVIRONMENT") != "test":
        raise ImproperlyConfigured("Injected OTP delivery is allowed only in tests.")
    provider = delivery if delivery is not None else configured_delivery()
    throttle("source:" + source, limit=10, seconds=600)
    throttle("phone:" + phone, limit=1, seconds=60)
    now = timezone.now()
    latest = OTPChallenge.objects.filter(phone=phone).order_by("-created_at").first()
    if latest and latest.created_at + timedelta(seconds=60) > now:
        raise ValidationError("Please wait before requesting another code.")
    code = f"{secrets.randbelow(1000000):06d}"
    challenge = OTPChallenge.objects.create(
        phone=phone, code_hash=make_password(code), expires_at=now + timedelta(minutes=5)
    )
    try:
        provider.deliver(phone, code)
    except (OSError, ImproperlyConfigured):
        OTPChallenge.objects.filter(pk=challenge.pk).update(consumed_at=timezone.now())
        raise
    return challenge


def verify_otp(challenge_id: UUID, code: str) -> Account:
    invalid = False
    with transaction.atomic():
        challenge = OTPChallenge.objects.select_for_update().get(pk=challenge_id)
        if challenge.consumed_at or challenge.expires_at <= timezone.now() or challenge.attempts >= 5:
            raise ValidationError("Code expired, exhausted or already used.")
        challenge.attempts += 1
        if not check_password(code, challenge.code_hash):
            invalid = True
            challenge.save(update_fields=["attempts"])
        else:
            challenge.consumed_at = timezone.now()
            challenge.save(update_fields=["attempts", "consumed_at"])
            account, _ = Account.objects.get_or_create(
                phone=challenge.phone, defaults={"username": challenge.phone, "password": make_password(None)}
            )
            if not account.is_active or account.is_doctor:
                raise ValidationError("This account cannot use patient sign-in.")
    if invalid:
        raise ValidationError("Code is incorrect.")
    return account


@transaction.atomic
def hold_after_restore(actor: Account) -> None:
    from django.contrib.sessions.models import Session

    from accounts.models import AccessControl
    from audit.services import record
    from patients.permissions import require_doctor

    require_doctor(actor)
    AccessControl.objects.get_or_create(pk=1)
    control = AccessControl.objects.select_for_update().get(pk=1)
    control.patient_access_suspended = True
    control.save(update_fields=["patient_access_suspended"])
    Session.objects.all().delete()
    record(actor, "restore.patient_access_suspended", control)
