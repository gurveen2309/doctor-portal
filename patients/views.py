from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import redirect, render
from django.views.decorators.http import require_http_methods

from accounts.access import request_actor
from patients.forms import GrantForm, PatientForm, PhoneReviewForm, RevokeForm
from patients.models import Patient
from patients.permissions import require_doctor
from patients.services import create_patient, review_phone, revoke_grant, verify_grant


@require_http_methods(["GET", "POST"])
def manage(request: HttpRequest) -> HttpResponse:
    actor = request_actor(request)
    require_doctor(actor)
    forms = {
        "patient": PatientForm(),
        "phone": PhoneReviewForm(),
        "grant": GrantForm(),
        "revoke": RevokeForm(),
    }
    if request.method == "POST":
        action = request.POST.get("action", "")
        if action not in forms:
            return HttpResponse("Invalid verification action.", status=400)
        form = type(forms[action])(request.POST)
        forms[action] = form
        if form.is_valid():
            data = form.cleaned_data
            try:
                if action == "patient":
                    create_patient(actor, **data)
                elif action == "phone":
                    review_phone(actor, data["account"], data["control"])
                elif action == "grant":
                    verify_grant(actor, **data)
                else:
                    revoke_grant(actor, data["grant"])
            except ValidationError as error:
                form.add_error(None, error)
            else:
                return redirect("manage-patients")
    return render(request, "patients/manage.html", {"forms": forms, "patients": Patient.objects.all()})
