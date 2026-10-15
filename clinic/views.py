import secrets

from django.contrib import messages
from django.core.exceptions import ValidationError
from django.core.paginator import Paginator
from django.db import transaction
from django.db.models import Q
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from accounts.access import request_actor
from appointments.models import Appointment
from audit.services import record
from clinic.forms import AvailabilityForm, DoctorIntakeForm, ProfileForm, RemoveClosureForm, RemoveWindowForm
from clinic.models import AvailabilityWindow, ClinicProfile, Closure
from clinic.services import lock_calendar, publish_window
from intake.models import ClinicRequest
from intake.services import submit_request
from patients.permissions import require_doctor


@require_http_methods(["GET"])
def public(request: HttpRequest) -> HttpResponse:
    return render(
        request,
        "clinic/public.html",
        {"profile": ClinicProfile.objects.filter(pk=1).first(), "closures": Closure.objects.all()},
    )


@require_http_methods(["GET"])
def workspace(request: HttpRequest) -> HttpResponse:
    require_doctor(request_actor(request))
    view = request.GET.get("view", "queue")
    if view not in {"queue", "history"}:
        return HttpResponse("Unknown request view.", status=400)
    rows = ClinicRequest.objects.select_related("patient", "fulfillment")
    if view == "queue":
        rows = rows.filter(
            Q(status__in=["received", "missing_information", "alternative_proposed", "approved"])
            | Q(change_requested=True)
            | Q(fulfillment__cancellation_pending=True)
        )
    else:
        rows = rows.order_by("-created_at")
    page = Paginator(rows, 50).get_page(request.GET.get("page"))
    return render(
        request,
        "clinic/workspace.html",
        {
            "page": page,
            "queue_view": view,
            "appointments": Appointment.objects.filter(status="confirmed")
            .select_related("patient")
            .order_by("starts_at"),
            "windows": AvailabilityWindow.objects.order_by("starts_at"),
        },
    )


@require_http_methods(["GET", "POST"])
def settings_view(request: HttpRequest) -> HttpResponse:
    actor = request_actor(request)
    require_doctor(actor)
    profile, _ = ClinicProfile.objects.get_or_create(pk=1)
    profile_form = ProfileForm(request.POST if request.POST.get("action") == "profile" else None, instance=profile)
    window_form = AvailabilityForm(request.POST if request.POST.get("action") == "window" else None)
    remove_form = RemoveWindowForm(request.POST if request.POST.get("action") == "remove" else None)
    closure_form = RemoveClosureForm(request.POST if request.POST.get("action") == "open" else None)
    forms = {"profile": profile_form, "window": window_form, "remove": remove_form, "open": closure_form}
    if request.method == "POST":
        action = request.POST.get("action", "")
        if action not in forms:
            return HttpResponse("Invalid settings action.", status=400)
        form = forms[action]
        if form.is_valid():
            try:
                with transaction.atomic():
                    lock_calendar()
                    if action == "profile":
                        saved = profile_form.save()
                        record(actor, "clinic.profile_changed", saved)
                    elif action == "window":
                        publish_window(actor, **window_form.cleaned_data)
                    elif action == "remove":
                        window = remove_form.cleaned_data["window"]
                        if Appointment.objects.filter(
                            status="confirmed", starts_at__lt=window.ends_at, ends_at__gt=window.starts_at
                        ).exists():
                            raise ValidationError("This window intersects confirmed bookings; reconcile them first.")
                        record(actor, "calendar.window_removed", window)
                        window.delete()
                    else:
                        closure = closure_form.cleaned_data["closure"]
                        record(actor, "calendar.closure_removed", closure)
                        closure.delete()
            except ValidationError as error:
                form.add_error(None, error)
            else:
                return redirect("clinic-settings")
    return render(request, "clinic/settings.html", {"forms": forms})


@require_http_methods(["GET", "POST"])
def doctor_intake(request: HttpRequest) -> HttpResponse:
    actor = request_actor(request)
    require_doctor(actor)
    form = DoctorIntakeForm(
        request.POST or None, initial={"idempotency_key": secrets.token_hex(16), "preference": "pickup"}
    )
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data.copy()
        patient = data.pop("patient")
        try:
            row = submit_request(actor, patient, **data)
        except ValidationError as error:
            form.add_error(None, error)
        else:
            return redirect("doctor-request", request_id=row.pk)
    return render(request, "intake/form.html", {"form": form, "title": "Phone / in-person intake"})
