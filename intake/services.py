import hashlib
import json
from datetime import datetime

from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction

from accounts.models import Account
from audit.services import record
from clinic.services import validate_interval
from intake.models import ClinicRequest
from patients.models import Patient
from patients.permissions import require_access, require_doctor


@transaction.atomic
def submit_request(
    actor: Account,
    patient: Patient,
    kind: str,
    *,
    idempotency_key: str,
    channel: str = "portal",
    message: str = "",
    time_sensitive: bool = False,
    reason: str = "",
    starts_at: datetime | None = None,
    ends_at: datetime | None = None,
    preference: str = "pickup",
    delivery_address: str = "",
) -> ClinicRequest:
    require_access(actor, patient, "clinical" if kind == "clarification" else "admin")
    if kind not in {"appointment", "clarification", "repeat"}:
        raise ValidationError("Choose a valid request type.")
    if channel not in {"portal", "phone", "in_person"}:
        raise ValidationError("Choose a valid intake channel.")
    if channel != "portal":
        require_doctor(actor)
    if time_sensitive and not reason.strip():
        raise ValidationError("A time-sensitive request requires a reason.")
    if not idempotency_key or len(idempotency_key) > 64:
        raise ValidationError("A valid submission key is required.")
    if kind == "appointment":
        if starts_at is None or ends_at is None:
            raise ValidationError("Requested start and end are required.")
        validate_interval(starts_at, ends_at)
    if preference not in {"pickup", "delivery"} or (preference == "delivery" and not delivery_address.strip()):
        raise ValidationError("Delivery requires a minimal address; otherwise select pickup.")
    data = {
        "patient_id": patient.pk,
        "kind": kind,
        "channel": channel,
        "message": message,
        "time_sensitive": time_sensitive,
        "reason": reason,
        "starts_at": starts_at,
        "ends_at": ends_at,
        "preference": preference,
        "delivery_address": delivery_address if preference == "delivery" else "",
    }
    digest = hashlib.sha256(json.dumps(data, default=str, sort_keys=True).encode()).hexdigest()
    row, created = ClinicRequest.objects.get_or_create(
        actor=actor, idempotency_key=idempotency_key, defaults={**data, "payload_digest": digest}
    )
    if row.payload_digest != digest:
        raise ValidationError("Submission key conflicts with different request content.")
    if created:
        record(actor, "request.received", row)
    return row


@transaction.atomic
def set_priority(actor: Account, request: ClinicRequest, priority: int) -> None:
    require_doctor(actor)
    if priority not in {0, 1, 2}:
        raise ValidationError("Priority must be routine, elevated or first.")
    row = ClinicRequest.objects.select_for_update().get(pk=request.pk)
    row.priority = priority
    row.save(update_fields=["priority"])
    record(actor, "request.prioritized", row)
