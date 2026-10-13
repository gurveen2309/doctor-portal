from django import forms as django_forms
from django.contrib import messages
from django.core.exceptions import ValidationError
from django.http import HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.views.decorators.http import require_http_methods

from accounts.access import request_actor
from operations.forms import ChargeCorrectionForm, ChargeForm, ReceiptCorrectionForm, ReceiptForm
from operations.models import Charge, ReceiptEntry
from operations.services import (
    correct_charge,
    correct_receipt,
    receipt_status,
    received_total,
    record_charge,
    record_receipt,
)
from patients.models import Patient
from patients.permissions import require_doctor, require_visible_access


@require_http_methods(["GET", "POST"])
def payments(request: HttpRequest, patient_id: int) -> HttpResponse:
    actor = request_actor(request)
    patient = get_object_or_404(Patient, pk=patient_id)
    require_visible_access(actor, patient, "admin")
    forms = {
        "charge": ChargeForm(),
        "receipt": ReceiptForm(),
        "charge_correction": ChargeCorrectionForm(),
        "receipt_correction": ReceiptCorrectionForm(),
    }
    if request.method == "POST":
        require_doctor(actor)
        action = request.POST.get("action", "")
        if action not in forms:
            return HttpResponse("Invalid payment record action.", status=400)
        forms[action] = type(forms[action])(request.POST)
    for form in forms.values():
        charge_field = form.fields.get("charge")
        receipt_field = form.fields.get("receipt")
        if isinstance(charge_field, django_forms.ModelChoiceField):
            charge_field.queryset = Charge.objects.filter(patient=patient)
        if isinstance(receipt_field, django_forms.ModelChoiceField):
            receipt_field.queryset = ReceiptEntry.objects.filter(charge__patient=patient)
    if request.method == "POST":
        form = forms[action]
        if form.is_valid():
            try:
                data = form.cleaned_data
                if action == "charge":
                    record_charge(actor, patient, **data)
                elif action == "receipt":
                    record_receipt(actor, **data)
                elif action == "charge_correction":
                    correct_charge(actor, **data)
                else:
                    correct_receipt(actor, **data)
            except ValidationError as error:
                form.add_error(None, error)
            else:
                messages.success(request, "Manual external payment record saved. No payment or refund was executed.")
                return redirect("patient-payments", patient_id=patient.pk)
    rows = [
        {"charge": row, "received": received_total(row), "status": receipt_status(row).replace("_", " ").title()}
        for row in Charge.objects.filter(patient=patient)
    ]
    return render(
        request,
        "operations/payments.html",
        {"patient": patient, "rows": rows, "forms": forms if actor.is_doctor else {}},
    )
