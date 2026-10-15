from decimal import Decimal
from urllib.parse import urlsplit

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.db import transaction
from django.db.models import Sum

from accounts.models import Account
from appointments.services import cancel_request
from audit.services import record
from clinical.models import RepeatDecision
from intake.models import ClinicRequest
from operations.models import Charge, ChargeCorrection, Fulfillment, ReceiptEntry
from patients.models import Patient
from patients.permissions import require_access, require_doctor


@transaction.atomic
def advance_fulfillment(
    actor: Account,
    request: ClinicRequest,
    status: str,
    *,
    carrier: str = "",
    tracking_number: str = "",
    tracking_link: str = "",
) -> Fulfillment:
    require_doctor(actor)
    row = ClinicRequest.objects.select_for_update().get(pk=request.pk)
    if row.kind != "repeat" or row.status not in {"approved", "fulfilled"}:
        raise ValidationError("An approved medicine repeat is required.")
    if not RepeatDecision.objects.filter(request=row, outcome="approve").exists():
        raise ValidationError("Explicit doctor approval is required.")
    if tracking_link:
        URLValidator(schemes=["https"])(tracking_link)
        parsed = urlsplit(tracking_link)
        if parsed.username or parsed.password:
            raise ValidationError("Tracking links must not contain credentials.")
    fulfillment, _ = Fulfillment.objects.get_or_create(request=row, defaults={"actor": actor})
    permitted = {
        "approved": {"preparing", "cancelled"},
        "preparing": {"ready", "dispatched"},
        "ready": {"dispatched", "delivered"},
        "dispatched": {"delivered"},
        "delivered": set(),
        "cancelled": set(),
    }
    if status not in permitted.get(fulfillment.status, set()):
        raise ValidationError("Invalid fulfillment transition; physical cancellation requires review.")
    if status == "dispatched" and (not carrier.strip() or not (tracking_number.strip() or tracking_link)):
        raise ValidationError("Record a carrier and tracking number or HTTPS link for manual dispatch.")
    fulfillment.status, fulfillment.actor = status, actor
    if carrier:
        fulfillment.carrier = carrier
    if tracking_number:
        fulfillment.tracking_number = tracking_number
    if tracking_link:
        fulfillment.tracking_link = tracking_link
    fulfillment.save()
    if status in {"delivered", "cancelled"}:
        row.status = "fulfilled" if status == "delivered" else "cancelled"
        row.save(update_fields=["status"])
    record(actor, "fulfillment." + status, fulfillment)
    return fulfillment


@transaction.atomic
def request_cancellation(actor: Account, request: ClinicRequest) -> None:
    require_access(actor, request.patient, "clinical" if request.kind == "clarification" else "admin")
    if request.kind == "appointment":
        cancel_request(actor, request)
        return
    row = ClinicRequest.objects.select_for_update().get(pk=request.pk)
    fulfillment = Fulfillment.objects.filter(request=row).first()
    if fulfillment and fulfillment.status in {"preparing", "ready", "dispatched", "delivered"}:
        fulfillment.cancellation_pending = True
        fulfillment.save(update_fields=["cancellation_pending"])
        record(actor, "cancellation.review_requested", fulfillment)
    else:
        if row.status in {"cancelled", "fulfilled"}:
            raise ValidationError("This request cannot be cancelled automatically.")
        row.status = "cancelled"
        row.save(update_fields=["status"])
        if fulfillment:
            fulfillment.status = "cancelled"
            fulfillment.save(update_fields=["status"])
        record(actor, "request.cancelled", row)


@transaction.atomic
def review_cancellation(actor: Account, fulfillment: Fulfillment, *, cancel: bool) -> None:
    require_doctor(actor)
    ClinicRequest.objects.select_for_update().get(pk=fulfillment.request_id)
    row = Fulfillment.objects.select_for_update().get(pk=fulfillment.pk)
    if not row.cancellation_pending:
        raise ValidationError("No physical cancellation review is pending.")
    row.cancellation_pending = False
    if cancel:
        row.status = "cancelled"
        row.request.status = "cancelled"
        row.request.save(update_fields=["status"])
    row.actor = actor
    row.save()
    record(actor, "cancellation.approved" if cancel else "cancellation.declined", row)


def valid_amount(amount: Decimal) -> None:
    if (
        not amount.is_finite()
        or amount < 0
        or amount > Decimal("99999999.99")
        or amount != amount.quantize(Decimal(".01"))
    ):
        raise ValidationError("Enter a non-negative INR amount with at most two decimal places.")


@transaction.atomic
def record_charge(actor: Account, patient: Patient, category: str, amount: Decimal) -> Charge:
    require_doctor(actor)
    valid_amount(amount)
    if category not in {"consultation", "medicine", "delivery"}:
        raise ValidationError("Choose consultation, medicine or delivery.")
    charge = Charge.objects.create(patient=patient, category=category, amount=amount, actor=actor)
    record(actor, "charge.recorded", charge)
    return charge


@transaction.atomic
def correct_charge(actor: Account, charge: Charge, amount: Decimal) -> ChargeCorrection:
    require_doctor(actor)
    valid_amount(amount)
    current = Charge.objects.select_for_update().get(pk=charge.pk)
    correction = ChargeCorrection.objects.create(
        charge=current, previous_amount=current.amount, amount=amount, actor=actor
    )
    current.amount = amount
    current.save(update_fields=["amount"])
    record(actor, "charge.corrected", correction)
    return correction


@transaction.atomic
def record_receipt(actor: Account, charge: Charge, amount: Decimal, method: str) -> ReceiptEntry:
    require_doctor(actor)
    valid_amount(amount)
    if method not in {"cash", "upi"}:
        raise ValidationError("Record externally received cash or UPI only.")
    receipt = ReceiptEntry.objects.create(charge=charge, amount=amount, method=method, actor=actor)
    record(actor, "receipt.recorded", receipt)
    return receipt


@transaction.atomic
def correct_receipt(actor: Account, receipt: ReceiptEntry, amount: Decimal) -> ReceiptEntry:
    require_doctor(actor)
    valid_amount(amount)
    current = ReceiptEntry.objects.select_for_update().get(pk=receipt.pk)
    if ReceiptEntry.objects.filter(corrects=current).exists():
        raise ValidationError("Correct the latest receipt revision, not a superseded entry.")
    correction = ReceiptEntry.objects.create(
        charge=current.charge, amount=amount, method=current.method, actor=actor, corrects=current
    )
    record(actor, "receipt.corrected", correction)
    return correction


def received_total(charge: Charge) -> Decimal:
    superseded = ReceiptEntry.objects.filter(charge=charge, corrects__isnull=False).values("corrects_id")
    amount = charge.receipts.exclude(pk__in=superseded).aggregate(total=Sum("amount"))["total"]
    return amount if amount is not None else Decimal("0")


def receipt_status(charge: Charge) -> str:
    received = received_total(charge)
    if received > charge.amount:
        return "over_recorded"
    if charge.amount == 0:
        return "no_charge"
    if received == 0:
        return "not_recorded"
    if received < charge.amount:
        return "partially_recorded"
    return "fully_recorded"
