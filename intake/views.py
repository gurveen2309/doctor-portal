import secrets

from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import IntegrityError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from accounts.access import request_actor
from appointments.models import Appointment, AppointmentProposal
from appointments.services import accept_proposal, request_change
from clinical.services import provide_information
from intake.forms import InformationForm, IntervalForm, RequestForm
from intake.models import ClinicRequest
from intake.services import submit_request
from operations.models import Fulfillment
from operations.services import request_cancellation
from patients.models import Patient
from patients.permissions import can_access, require_visible_access


def summary(row: ClinicRequest) -> dict[str, object]:
    return {
        "id": row.pk,
        "kind": row.get_kind_display(),
        "status": row.status.replace("_", " ").title(),
        "created_at": row.created_at,
        "time_sensitive": row.time_sensitive,
        "change_requested": row.change_requested,
    }


@require_http_methods(["GET"])
def portal(request: HttpRequest) -> HttpResponse:
    actor = request_actor(request)
    patients = [
        patient
        for patient in Patient.objects.filter(grants__account=actor).distinct()
        if can_access(actor, patient, "admin") or can_access(actor, patient, "clinical")
    ]
    return render(request, "intake/portal.html", {"patients": patients})


@require_http_methods(["GET"])
def patient_home(request: HttpRequest, patient_id: int) -> HttpResponse:
    actor = request_actor(request)
    patient = get_object_or_404(Patient, pk=patient_id)
    admin_access = can_access(actor, patient, "admin")
    if not admin_access:
        require_visible_access(actor, patient, "clinical")
    visible = ClinicRequest.objects.filter(patient=patient)
    if not admin_access:
        visible = visible.filter(kind="clarification")
    rows = [summary(row) for row in visible]
    return render(
        request,
        "intake/patient.html",
        {
            "patient": patient,
            "rows": rows,
            "admin_access": admin_access,
            "clinical_access": can_access(actor, patient, "clinical"),
        },
    )


@require_http_methods(["GET", "POST"])
def new_request(request: HttpRequest, patient_id: int) -> HttpResponse:
    actor = request_actor(request)
    patient = get_object_or_404(Patient, pk=patient_id)
    if request.method == "POST":
        require_visible_access(actor, patient, "clinical" if request.POST.get("kind") == "clarification" else "admin")
    elif not can_access(actor, patient, "admin"):
        require_visible_access(actor, patient, "clinical")
    form = RequestForm(request.POST or None, initial={"idempotency_key": secrets.token_hex(16), "preference": "pickup"})
    if request.method == "POST" and form.is_valid():
        try:
            row = submit_request(actor, patient, **form.cleaned_data)
        except ValidationError as error:
            form.add_error(None, error)
        else:
            if row.status == "received":
                messages.success(request, "Received / awaiting review.")
            else:
                messages.info(request, f"Request already recorded. Current status: {summary(row)['status']}.")
            return redirect("request-detail", request_id=row.pk)
    return render(request, "intake/form.html", {"form": form, "title": "New request", "patient": patient})


@require_http_methods(["GET"])
def request_detail(request: HttpRequest, request_id: int) -> HttpResponse:
    actor = request_actor(request)
    row = get_object_or_404(ClinicRequest.objects.select_related("patient"), pk=request_id)
    if row.kind == "clarification" and not can_access(actor, row.patient, "admin"):
        require_visible_access(actor, row.patient, "clinical")
    else:
        require_visible_access(actor, row.patient, "admin")
    clinical_access = can_access(actor, row.patient, "clinical")
    fulfillment = Fulfillment.objects.filter(request=row).first()
    return render(
        request,
        "intake/detail.html",
        {
            "summary": summary(row),
            "patient": row.patient,
            "private": row if clinical_access else None,
            "responses": row.responses.all() if clinical_access else [],
            "proposals": AppointmentProposal.objects.filter(request=row, state="proposed"),
            "appointments": Appointment.objects.filter(request=row, status="confirmed"),
            "change_form": IntervalForm(),
            "information_form": InformationForm(),
            "fulfillment_status": fulfillment.status.title() if fulfillment else "",
            "cancellation_pending": fulfillment.cancellation_pending if fulfillment else False,
        },
    )


@require_POST
def accept(request: HttpRequest, proposal_id: int) -> HttpResponse:
    actor = request_actor(request)
    proposal = get_object_or_404(AppointmentProposal.objects.select_related("request__patient"), pk=proposal_id)
    require_visible_access(actor, proposal.request.patient, "admin")
    try:
        appointment = accept_proposal(actor, proposal)
    except (ValidationError, IntegrityError):
        require_visible_access(actor, proposal.request.patient, "admin")
        messages.error(request, "The alternative is no longer available. Your original booking, if any, is unchanged.")
    else:
        messages.success(request, "Appointment confirmed.")
    return redirect("request-detail", request_id=proposal.request_id)


@require_POST
def change(request: HttpRequest, request_id: int) -> HttpResponse:
    actor = request_actor(request)
    row = get_object_or_404(ClinicRequest, pk=request_id)
    require_visible_access(actor, row.patient, "admin")
    form = IntervalForm(request.POST)
    if not form.is_valid():
        return render(request, "intake/form.html", {"form": form, "title": "Request appointment change"}, status=400)
    try:
        request_change(actor, row, **form.cleaned_data)
    except ValidationError as error:
        form.add_error(None, error)
        return render(request, "intake/form.html", {"form": form, "title": "Request appointment change"}, status=400)
    messages.success(request, "Change received. Your confirmed booking stays until a valid replacement is accepted.")
    return redirect("request-detail", request_id=row.pk)


@require_POST
def cancel(request: HttpRequest, request_id: int) -> HttpResponse:
    actor = request_actor(request)
    row = get_object_or_404(ClinicRequest, pk=request_id)
    require_visible_access(actor, row.patient, "clinical" if row.kind == "clarification" else "admin")
    try:
        request_cancellation(actor, row)
    except ValidationError as error:
        messages.error(request, "; ".join(error.messages))
    else:
        messages.success(request, "Cancellation recorded or awaiting physical-work review.")
    return redirect("request-detail", request_id=row.pk)


@require_POST
def information(request: HttpRequest, request_id: int) -> HttpResponse:
    actor = request_actor(request)
    row = get_object_or_404(ClinicRequest, pk=request_id)
    require_visible_access(actor, row.patient, "clinical")
    form = InformationForm(request.POST)
    if form.is_valid():
        try:
            provide_information(actor, row, form.cleaned_data["message"])
        except ValidationError as error:
            form.add_error(None, error)
        else:
            return redirect("request-detail", request_id=row.pk)
    return render(request, "intake/form.html", {"form": form, "title": "Missing clinical information"}, status=400)
