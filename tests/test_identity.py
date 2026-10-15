import importlib.util
from datetime import date, timedelta

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.utils import timezone

pytestmark = pytest.mark.django_db


def identity_modules() -> None:
    assert importlib.util.find_spec("accounts") is not None, "Verified accounts are not implemented"
    assert importlib.util.find_spec("patients") is not None, "Patient grant authorization is not implemented"


def identities():
    identity_modules()
    from django_otp.plugins.otp_totp.models import TOTPDevice

    from accounts.models import Account
    from patients.models import Patient

    doctor = Account.objects.create_user(username="doctor", phone="+919000000001", is_doctor=True)
    doctor.otp_device = TOTPDevice.objects.create(user=doctor, confirmed=True)
    patient = Patient.objects.create(card_number="OLD-1", name="Synthetic Adult", verified_by=doctor)
    user = Account.objects.create_user(
        username="patient", phone="+919000000002", phone_control="private", phone_reviewed_at=timezone.now()
    )
    return doctor, patient, user


def test_card_number_does_not_authorize_access() -> None:
    _, patient, user = identities()
    from patients.permissions import require_access

    with pytest.raises(PermissionDenied):
        require_access(user, patient, "admin")


@pytest.mark.parametrize(
    ("control", "clinical", "scope", "allowed"),
    [
        ("shared", False, "admin", True),
        ("shared", True, "clinical", False),
        ("private", False, "clinical", False),
        ("private", True, "clinical", True),
        ("unreviewed", True, "clinical", False),
    ],
)
def test_adult_permission_matrix(control: str, clinical: bool, scope: str, allowed: bool) -> None:
    doctor, patient, user = identities()
    from patients.models import AccessGrant
    from patients.permissions import require_access

    user.phone_control = control
    user.save()
    AccessGrant.objects.create(account=user, patient=patient, admin=True, clinical=clinical, verified_by=doctor)
    if allowed:
        require_access(user, patient, scope)
    else:
        with pytest.raises(PermissionDenied):
            require_access(user, patient, scope)


def test_revocation_is_immediate_for_existing_user_instance() -> None:
    doctor, patient, user = identities()
    from patients.models import AccessGrant
    from patients.permissions import require_access

    grant = AccessGrant.objects.create(account=user, patient=patient, admin=True, clinical=True, verified_by=doctor)
    require_access(user, patient, "clinical")
    grant.revoked_at = timezone.now()
    grant.save()
    with pytest.raises(PermissionDenied):
        require_access(user, patient, "clinical")


def test_guardian_clinical_access_stops_at_eighteen() -> None:
    doctor, patient, user = identities()
    from patients.models import AccessGrant
    from patients.permissions import require_access

    today = timezone.localdate()
    patient.date_of_birth = date(today.year - 18, today.month, today.day)
    patient.save()
    AccessGrant.objects.create(
        account=user, patient=patient, admin=True, clinical=True, relationship="guardian", verified_by=doctor
    )
    with pytest.raises(PermissionDenied):
        require_access(user, patient, "clinical")
    patient.date_of_birth += timedelta(days=1)
    patient.save()
    require_access(user, patient, "clinical")


def test_guardian_missing_dob_and_self_verification_are_rejected() -> None:
    doctor, patient, user = identities()
    from patients.services import verify_grant

    with pytest.raises(ValidationError):
        verify_grant(doctor, user, patient, admin=True, clinical=True, relationship="guardian")
    with pytest.raises(PermissionDenied):
        verify_grant(user, user, patient, admin=True, clinical=False, relationship="self")


def test_unverified_patient_and_grant_are_denied() -> None:
    doctor, patient, user = identities()
    from patients.models import AccessGrant
    from patients.permissions import require_access

    AccessGrant.objects.create(account=user, patient=patient, admin=True)
    with pytest.raises(PermissionDenied):
        require_access(user, patient, "admin")
    patient.verified_by = None
    patient.save()
    with pytest.raises(PermissionDenied):
        require_access(user, patient, "admin")


def test_password_only_doctor_is_denied_and_audit_has_no_text() -> None:
    doctor, patient, _ = identities()
    from audit.models import AuditEvent
    from patients.permissions import require_doctor
    from patients.services import verify_patient

    verify_patient(doctor, patient)
    event = AuditEvent.objects.get(action="patient.verified")
    assert event.record_id == str(patient.pk)
    assert {field.name for field in event._meta.fields} == {
        "id",
        "actor",
        "action",
        "record_type",
        "record_id",
        "created_at",
    }
    with pytest.raises(ValidationError):
        event.delete()
    with pytest.raises(ValidationError):
        AuditEvent.objects.all().update(action="altered")
    doctor.otp_device = None
    with pytest.raises(PermissionDenied):
        require_doctor(doctor)


def test_review_required_and_downgrade_rechecked() -> None:
    doctor, patient, user = identities()
    from patients.models import AccessGrant
    from patients.permissions import require_access
    from patients.services import review_phone

    AccessGrant.objects.create(account=user, patient=patient, clinical=True, verified_by=doctor)
    user.phone_reviewed_at = None
    user.save()
    with pytest.raises(PermissionDenied):
        require_access(user, patient, "clinical")
    review_phone(doctor, user, "private")
    require_access(user, patient, "clinical")
    review_phone(doctor, user, "shared")
    with pytest.raises(PermissionDenied):
        require_access(user, patient, "clinical")


def test_patient_creation_preserves_unique_cards() -> None:
    doctor, _, _ = identities()
    from patients.services import create_patient

    migrated = create_patient(doctor, name="Synthetic migration", card_number="PAPER-87")
    assert migrated.card_number == "PAPER-87"
    new = create_patient(doctor, name="Synthetic new")
    assert new.card_number != migrated.card_number
    with pytest.raises(ValidationError):
        create_patient(doctor, name="Duplicate", card_number="PAPER-87")


def test_doctor_verification_routes_enforce_mfa(client) -> None:
    doctor, patient, user = identities()
    client.force_login(doctor)
    assert client.get("/patients/manage/").status_code == 403
    assert client.post("/patients/manage/", {"patient": patient.pk, "action": "verify"}).status_code == 403
