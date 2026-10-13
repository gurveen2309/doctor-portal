import importlib.util
from decimal import Decimal

import pytest
from django.core.exceptions import ValidationError

from tests.test_calendar import calendar_data

pytestmark = pytest.mark.django_db


def operations_services():
    assert importlib.util.find_spec("operations") is not None, "Manual operations are not implemented"
    from operations import services

    return services


def test_fulfillment_needs_approval_and_physical_cancellation_is_reviewed() -> None:
    doctor, patient, user, _, _, _ = calendar_data()
    service = operations_services()
    from clinical.services import decide_repeat
    from intake.services import submit_request

    repeat = submit_request(user, patient, "repeat", idempotency_key="medicine")
    with pytest.raises(ValidationError):
        service.advance_fulfillment(doctor, repeat, "preparing")
    decide_repeat(doctor, repeat, "approve")
    service.advance_fulfillment(doctor, repeat, "preparing")
    with pytest.raises(ValidationError):
        service.advance_fulfillment(doctor, repeat, "dispatched", tracking_link="http://unsafe.example")
    dispatched = service.advance_fulfillment(
        doctor, repeat, "dispatched", carrier="Manual carrier", tracking_number="SYNTHETIC"
    )
    service.request_cancellation(user, repeat)
    dispatched.refresh_from_db()
    assert dispatched.status == "dispatched" and dispatched.cancellation_pending


def test_charge_receipt_and_audited_correction_are_distinct() -> None:
    doctor, patient, _, _, _, _ = calendar_data()
    service = operations_services()
    from operations.models import ReceiptEntry

    charge = service.record_charge(doctor, patient, "medicine", Decimal("300.00"))
    assert service.received_total(charge) == Decimal("0")
    receipt = service.record_receipt(doctor, charge, Decimal("200.00"), "upi")
    corrected = service.correct_receipt(doctor, receipt, Decimal("150.00"))
    assert service.received_total(charge) == Decimal("150.00")
    assert ReceiptEntry.objects.get(pk=receipt.pk).amount == Decimal("200.00")
    assert corrected.corrects_id == receipt.pk
    with pytest.raises(ValidationError):
        service.record_receipt(doctor, charge, Decimal("-1.00"), "cash")


def test_manual_status_is_based_on_recorded_external_amounts_only() -> None:
    doctor, patient, _, _, _, _ = calendar_data()
    service = operations_services()
    charge = service.record_charge(doctor, patient, "medicine", Decimal("100.00"))
    assert hasattr(service, "receipt_status"), "Recorded receipt status is not implemented"
    assert service.receipt_status(charge) == "not_recorded"
    service.record_receipt(doctor, charge, Decimal("30.00"), "cash")
    assert service.receipt_status(charge) == "partially_recorded"
    service.record_receipt(doctor, charge, Decimal("70.00"), "upi")
    assert service.receipt_status(charge) == "fully_recorded"
    service.record_receipt(doctor, charge, Decimal("1.00"), "cash")
    assert service.receipt_status(charge) == "over_recorded"
