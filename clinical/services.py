from datetime import date

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Max
from django.utils import timezone

from accounts.models import Account
from audit.services import record
from clinical.models import ClarificationResponse, InstructionRevision, RepeatDecision, Visit
from intake.models import ClinicRequest
from patients.models import Patient
from patients.permissions import require_access, require_doctor


@transaction.atomic
def record_visit(actor: Account, patient: Patient, *, follow_up_date: date | None = None) -> Visit:
    require_doctor(actor)
    require_access(actor, patient, "clinical")
    if follow_up_date and follow_up_date < timezone.localdate():
        raise ValidationError("Choose an explicit current or future follow-up date.")
    visit = Visit.objects.create(patient=patient, actor=actor, follow_up_date=follow_up_date)
    record(actor, "visit.recorded", visit)
    return visit


@transaction.atomic
def revise_instructions(
    actor: Account, visit: Visit, *, medicine: str, precautions: str, diet: str
) -> InstructionRevision:
    require_doctor(actor)
    current = Visit.objects.select_for_update().get(pk=visit.pk)
    latest = current.revisions.aggregate(last=Max("revision"))["last"] or 0
    revision = InstructionRevision.objects.create(
        visit=current, revision=latest + 1, medicine=medicine, precautions=precautions, diet=diet, actor=actor
    )
    record(actor, "instructions.revised", revision)
    return revision


@transaction.atomic
def reply_clarification(actor: Account, request: ClinicRequest, outcome: str, message: str) -> ClarificationResponse:
    require_doctor(actor)
    row = ClinicRequest.objects.select_for_update().get(pk=request.pk)
    if row.kind != "clarification" or row.status == "cancelled":
        raise ValidationError("A live clarification is required.")
    if outcome not in {"reply", "missing_information", "consultation_required"} or not message.strip():
        raise ValidationError("Choose a clinical outcome and write a private response.")
    response = ClarificationResponse.objects.create(request=row, actor=actor, outcome=outcome, message=message)
    row.status = "replied" if outcome == "reply" else outcome
    row.save(update_fields=["status"])
    record(actor, "clarification.responded", response)
    return response


@transaction.atomic
def provide_information(actor: Account, request: ClinicRequest, message: str) -> ClarificationResponse:
    require_access(actor, request.patient, "clinical")
    row = ClinicRequest.objects.select_for_update().get(pk=request.pk)
    if row.kind != "clarification" or row.status != "missing_information" or not message.strip():
        raise ValidationError("This request is not awaiting missing clinical information.")
    response = ClarificationResponse.objects.create(
        request=row, actor=actor, outcome="patient_information", message=message
    )
    row.status = "received"
    row.save(update_fields=["status"])
    record(actor, "clarification.information_added", response)
    return response


@transaction.atomic
def decide_repeat(actor: Account, request: ClinicRequest, outcome: str) -> RepeatDecision:
    require_doctor(actor)
    row = ClinicRequest.objects.select_for_update().get(pk=request.pk)
    if (
        row.kind != "repeat"
        or row.status != "received"
        or outcome not in {"approve", "decline", "consultation_required"}
    ):
        raise ValidationError("Choose an explicit outcome for an undecided repeat request.")
    decision = RepeatDecision.objects.create(request=row, actor=actor, outcome=outcome)
    row.status = "approved" if outcome == "approve" else outcome
    row.save(update_fields=["status"])
    record(actor, "repeat.decided", decision)
    return decision
