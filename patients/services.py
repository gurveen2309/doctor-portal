import secrets
from datetime import date

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from accounts.models import Account
from audit.services import record
from patients.models import AccessGrant, Patient
from patients.permissions import is_child, require_doctor


@transaction.atomic
def verify_patient(actor: Account, patient: Patient) -> Patient:
    require_doctor(actor)
    current = Patient.objects.select_for_update().get(pk=patient.pk)
    current.verified_by, current.verified_at = actor, timezone.now()
    current.save()
    record(actor, "patient.verified", current)
    return current


@transaction.atomic
def create_patient(actor: Account, *, name: str, card_number: str = "", date_of_birth: date | None = None) -> Patient:
    require_doctor(actor)
    if not card_number:
        card_number = "P-" + secrets.token_hex(8).upper()
    patient = Patient(card_number=card_number, name=name, date_of_birth=date_of_birth)
    patient.full_clean()
    patient.save()
    return verify_patient(actor, patient)


@transaction.atomic
def review_phone(actor: Account, account: Account, control: str) -> None:
    require_doctor(actor)
    if control not in {"private", "shared"}:
        raise ValidationError("Choose reviewed private or shared phone control.")
    current = Account.objects.select_for_update().get(pk=account.pk)
    current.phone_control, current.phone_reviewed_at = control, timezone.now()
    current.save(update_fields=["phone_control", "phone_reviewed_at"])
    record(actor, "account.phone_reviewed", current)


@transaction.atomic
def verify_grant(
    actor: Account, account: Account, patient: Patient, *, admin: bool, clinical: bool, relationship: str
) -> AccessGrant:
    require_doctor(actor)
    current = Patient.objects.select_for_update().get(pk=patient.pk)
    if not current.verified_by_id:
        raise ValidationError("Verify the patient first.")
    if relationship not in {"self", "delegate", "guardian"} or not (admin or clinical):
        raise ValidationError("Choose an explicit valid relationship and scope.")
    if relationship == "guardian" and (not current.date_of_birth or not is_child(current)):
        raise ValidationError("Guardian authorization requires a child with DOB.")
    if clinical and relationship != "guardian":
        reviewed_account = Account.objects.get(pk=account.pk)
        if (
            relationship != "self"
            or reviewed_account.phone_control != "private"
            or reviewed_account.phone_reviewed_at is None
            or is_child(current)
        ):
            raise ValidationError("Adult clinical access needs reviewed personally controlled phone.")
    grant, _ = AccessGrant.objects.update_or_create(
        account=account,
        patient=current,
        defaults={
            "admin": admin,
            "clinical": clinical,
            "relationship": relationship,
            "verified_by": actor,
            "verified_at": timezone.now(),
            "revoked_at": None,
        },
    )
    record(actor, "grant.verified", grant)
    return grant


@transaction.atomic
def revoke_grant(actor: Account, grant: AccessGrant) -> None:
    require_doctor(actor)
    current = AccessGrant.objects.select_for_update().get(pk=grant.pk)
    current.revoked_at = timezone.now()
    current.save(update_fields=["revoked_at"])
    record(actor, "grant.revoked", current)
