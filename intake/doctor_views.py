from django import forms as django_forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.db import IntegrityError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods, require_POST

from accounts.access import request_actor
from appointments.models import Appointment
from appointments.services import confirm_requested, propose_alternative
from clinical.forms import RepeatForm, ReplyForm
from clinical.services import decide_repeat, reply_clarification
from intake.forms import IntervalForm, PriorityForm
from intake.models import ClinicRequest
from intake.services import set_priority
from operations.forms import FulfillmentForm
from operations.models import Fulfillment
from operations.services import advance_fulfillment, review_cancellation
from patients.permissions import require_doctor


@require_http_methods(["GET", "POST"])
def doctor_request(request: HttpRequest, request_id: int) -> HttpResponse:
    actor = request_actor(request)
    require_doctor(actor)
    row = get_object_or_404(ClinicRequest.objects.select_related("patient"), pk=request_id)
    forms: dict[str, django_forms.Form] = {}
    if row.kind == "appointment":
        forms["alternative"] = IntervalForm()
    elif row.kind == "clarification":
        forms["reply"] = ReplyForm()
    else:
        forms["repeat"] = RepeatForm()
        forms["fulfillment"] = FulfillmentForm()
    if request.method == "POST":
        action = request.POST.get("action", "")
        if action in {"confirm", "cancellation_approve", "cancellation_decline"}:
            try:
                if action == "confirm":
                    confirm_requested(actor, row)
                else:
                    fulfillment = get_object_or_404(Fulfillment, request=row)
                    review_cancellation(actor, fulfillment, cancel=action == "cancellation_approve")
            except (ValidationError, IntegrityError) as error:
                messages.error(
                    request,
                    "; ".join(error.messages) if isinstance(error, ValidationError) else "Calendar conflict; retry.",
                )
            else:
                return redirect("doctor-request", request_id=row.pk)
        elif action in forms:
            form = type(forms[action])(request.POST)
            forms[action] = form
            if form.is_valid():
                try:
                    data = form.cleaned_data
                    if action == "alternative":
                        original = Appointment.objects.filter(request=row, status="confirmed").first()
                        propose_alternative(actor, row, original=original, **data)
                    elif action == "reply":
                        reply_clarification(actor, row, **data)
                    elif action == "repeat":
                        decide_repeat(actor, row, data["outcome"])
                    else:
                        advance_fulfillment(actor, row, **data)
                except ValidationError as error:
                    form.add_error(None, error)
                else:
                    return redirect("doctor-request", request_id=row.pk)
        else:
            return HttpResponse("Invalid doctor action.", status=400)
    return render(
        request,
        "intake/doctor_detail.html",
        {
            "row": row,
            "forms": forms,
            "priority_form": PriorityForm(initial={"priority": row.priority}),
            "fulfillment": Fulfillment.objects.filter(request=row).first(),
        },
    )


@require_POST
def priority(request: HttpRequest, request_id: int) -> HttpResponse:
    actor = request_actor(request)
    require_doctor(actor)
    row = get_object_or_404(ClinicRequest, pk=request_id)
    form = PriorityForm(request.POST)
    if form.is_valid():
        set_priority(actor, row, form.cleaned_data["priority"])
    if request.headers.get("HX-Request") == "true":
        return render(
            request, "intake/priority.html", {"row": row, "priority_form": form}, status=200 if form.is_valid() else 400
        )
    if not form.is_valid():
        return render(request, "intake/form.html", {"form": form, "title": "Doctor priority"}, status=400)
    return redirect("doctor-request", request_id=row.pk)
