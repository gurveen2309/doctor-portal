from typing import TYPE_CHECKING

from django import forms

from clinic.models import AvailabilityWindow, ClinicProfile, Closure
from intake.forms import IntervalForm, RequestForm
from patients.models import Patient

if TYPE_CHECKING:
    ProfileModelForm = forms.ModelForm[ClinicProfile]
else:
    ProfileModelForm = forms.ModelForm


class ProfileForm(ProfileModelForm):
    map_link = forms.URLField(required=False, assume_scheme="https")

    class Meta:
        model = ClinicProfile
        fields = ["name", "address", "map_link", "contact", "doctor_name", "opening_hours"]


class AvailabilityForm(IntervalForm):
    closed = forms.BooleanField(required=False, label="Closure instead of availability")


class RemoveWindowForm(forms.Form):
    window = forms.ModelChoiceField(queryset=AvailabilityWindow.objects.all())


class RemoveClosureForm(forms.Form):
    closure = forms.ModelChoiceField(queryset=Closure.objects.all())


class DoctorIntakeForm(RequestForm):
    patient = forms.ModelChoiceField(queryset=Patient.objects.filter(verified_by__isnull=False))
    channel = forms.ChoiceField(choices=[("phone", "Phone"), ("in_person", "In person")])
