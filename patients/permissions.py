from calendar import monthrange
from datetime import date

from django.core.exceptions import PermissionDenied
from django.http import Http404
from django.utils import timezone

from accounts.models import AccessControl, Account
from patients.models import AccessGrant, Patient


def require_doctor(actor: Account) -> None:
    if (
        not actor.is_authenticated
        or not actor.is_verified()
        or not Account.objects.filter(pk=actor.pk, is_doctor=True, is_active=True).exists()
    ):
        raise PermissionDenied("Verified doctor MFA is required.")


def is_child(patient: Patient) -> bool:
    if patient.date_of_birth is None:
        return False
    dob = patient.date_of_birth
    year = dob.year + 18
    birthday = date(year, dob.month, min(dob.day, monthrange(year, dob.month)[1]))
    return timezone.localdate() < birthday


def require_access(actor: Account, patient: Patient, scope: str) -> None:
    if scope not in {"admin", "clinical"}:
        raise PermissionDenied("Invalid access scope.")
    if not actor.is_authenticated or not Account.objects.filter(pk=actor.pk, is_active=True).exists():
        raise PermissionDenied("Sign-in is required.")
    if actor.is_doctor:
        require_doctor(actor)
        return
    if AccessControl.objects.filter(pk=1, patient_access_suspended=True).exists():
        raise PermissionDenied("Patient access is suspended pending reconciliation.")
    current = Patient.objects.get(pk=patient.pk)
    grant = AccessGrant.objects.filter(
        account=actor, patient=current, verified_by__isnull=False, revoked_at__isnull=True
    ).first()
    if not current.verified_by_id or not grant or not getattr(grant, scope):
        raise PermissionDenied("A current verified grant is required.")
    if scope == "clinical":
        if grant.relationship == "guardian" and current.date_of_birth and is_child(current):
            return
        account = Account.objects.get(pk=actor.pk)
        if (
            grant.relationship != "self"
            or account.phone_control != "private"
            or account.phone_reviewed_at is None
            or is_child(current)
        ):
            raise PermissionDenied("Verified personal adult clinical access is required.")


def can_access(actor: Account, patient: Patient, scope: str) -> bool:
    try:
        require_access(actor, patient, scope)
    except PermissionDenied:
        return False
    return True


def require_visible_access(actor: Account, patient: Patient, scope: str) -> None:
    try:
        require_access(actor, patient, scope)
    except PermissionDenied:
        raise Http404("Record unavailable.") from None
