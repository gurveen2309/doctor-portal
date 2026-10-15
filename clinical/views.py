from django.core.exceptions import ValidationError
from django.db import transaction
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from accounts.access import request_actor
from clinical.forms import VisitForm
from clinical.models import Visit
from clinical.services import record_visit, revise_instructions
from patients.models import Patient
from patients.permissions import require_doctor, require_visible_access


@require_http_methods(["GET"])
def history(request: HttpRequest, patient_id: int) -> HttpResponse:
    actor = request_actor(request)
    patient = get_object_or_404(Patient, pk=patient_id)
    require_visible_access(actor, patient, "clinical")
    return render(
        request, "clinical/history.html", {"patient": patient, "visits": Visit.objects.filter(patient=patient)}
    )


@require_http_methods(["GET", "POST"])
def visit_entry(request: HttpRequest, patient_id: int, visit_id: int | None = None) -> HttpResponse:
    actor = request_actor(request)
    require_doctor(actor)
    patient = get_object_or_404(Patient, pk=patient_id)
    existing = get_object_or_404(Visit, pk=visit_id, patient=patient) if visit_id else None
    form = VisitForm(request.POST or None, initial={"follow_up_date": existing.follow_up_date if existing else None})
    if request.method == "POST" and form.is_valid():
        try:
            with transaction.atomic():
                visit = existing or record_visit(actor, patient, follow_up_date=form.cleaned_data["follow_up_date"])
                if existing and form.cleaned_data["follow_up_date"] != existing.follow_up_date:
                    raise ValidationError("Instruction revisions do not silently change the recorded follow-up date.")
                revise_instructions(
                    actor,
                    visit,
                    medicine=form.cleaned_data["medicine"],
                    precautions=form.cleaned_data["precautions"],
                    diet=form.cleaned_data["diet"],
                )
        except ValidationError as error:
            form.add_error(None, error)
        else:
            return redirect("clinical-history", patient_id=patient.pk)
    return render(request, "intake/form.html", {"form": form, "title": "Doctor visit / instruction revision"})
