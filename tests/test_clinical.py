import importlib.util
from concurrent.futures import ThreadPoolExecutor
from datetime import timedelta
from threading import Barrier

import pytest
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import close_old_connections, connection
from django.utils import timezone

from tests.test_calendar import calendar_data

pytestmark = pytest.mark.django_db


def clinical_services():
    assert importlib.util.find_spec("clinical") is not None, "Clinical workflows are not implemented"
    from clinical import services

    return services


def test_versioned_instructions_and_explicit_follow_up() -> None:
    doctor, patient, user, request, start, end = calendar_data()
    service = clinical_services()
    visit = service.record_visit(doctor, patient)
    assert visit.follow_up_date is None
    first = service.revise_instructions(doctor, visit, medicine="PRIVATE-ONE", precautions="Care", diet="Food")
    second = service.revise_instructions(doctor, visit, medicine="PRIVATE-TWO", precautions="New care", diet="New food")
    first.refresh_from_db()
    assert first.medicine == "PRIVATE-ONE" and second.revision == 2
    first.medicine = "Overwritten"
    with pytest.raises(ValidationError):
        first.save()
    with pytest.raises(PermissionDenied):
        service.revise_instructions(user, visit, medicine="Self advice", precautions="", diet="")


def test_clarification_and_explicit_repeat_decisions() -> None:
    doctor, patient, user, _, _, _ = calendar_data()
    service = clinical_services()
    from intake.services import submit_request

    clarification = submit_request(
        user, patient, "clarification", idempotency_key="clarify", message="PRIVATE-QUESTION"
    )
    reply = service.reply_clarification(doctor, clarification, "missing_information", "PRIVATE-REPLY")
    assert reply.outcome == "missing_information"
    repeat = submit_request(user, patient, "repeat", idempotency_key="repeat")
    assert repeat.status == "received"
    with pytest.raises(PermissionDenied):
        service.decide_repeat(user, repeat, "approve")
    decision = service.decide_repeat(doctor, repeat, "consultation_required")
    assert decision.actor_id == doctor.pk and decision.decided_at is not None
    repeat.refresh_from_db()
    assert repeat.status == "consultation_required"


def test_explicit_follow_up_date_is_retained_without_an_inferred_interval() -> None:
    doctor, patient, _, _, _, _ = calendar_data()
    follow_up = timezone.localdate() + timedelta(days=11)
    visit = clinical_services().record_visit(doctor, patient, follow_up_date=follow_up)
    visit.refresh_from_db()
    assert visit.follow_up_date == follow_up


@pytest.mark.django_db(transaction=True)
def test_concurrent_instruction_revisions_keep_both_sequential_versions() -> None:
    doctor, patient, _, _, _, _ = calendar_data()
    from django_otp.plugins.otp_totp.models import TOTPDevice

    from accounts.models import Account
    from clinical.models import InstructionRevision
    from clinical.services import revise_instructions

    assert connection.vendor == "postgresql"
    visit = clinical_services().record_visit(doctor, patient)
    barrier = Barrier(2)

    def revision(text: str) -> int:
        close_old_connections()
        try:
            actor = Account.objects.get(pk=doctor.pk)
            actor.otp_device = TOTPDevice.objects.get(pk=doctor.otp_device.pk)
            barrier.wait(timeout=10)
            return revise_instructions(actor, visit, medicine=text, precautions="", diet="").revision
        finally:
            connection.close()

    with ThreadPoolExecutor(max_workers=2) as pool:
        assert sorted(pool.map(revision, ["SYNTHETIC-ONE", "SYNTHETIC-TWO"])) == [1, 2]
    assert set(InstructionRevision.objects.filter(visit=visit).values_list("medicine", flat=True)) == {
        "SYNTHETIC-ONE",
        "SYNTHETIC-TWO",
    }
