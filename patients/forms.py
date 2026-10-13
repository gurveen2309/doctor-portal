from django import forms

from accounts.models import Account
from patients.models import AccessGrant, Patient


class PatientForm(forms.Form):
    name = forms.CharField(max_length=100)
    card_number = forms.CharField(max_length=40, required=False, label="Existing card number (blank for new)")
    date_of_birth = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))


class GrantForm(forms.Form):
    patient = forms.ModelChoiceField(queryset=Patient.objects.all())
    account = forms.ModelChoiceField(queryset=Account.objects.filter(is_doctor=False))
    relationship = forms.ChoiceField(choices=[("self", "Self"), ("delegate", "Delegate"), ("guardian", "Guardian")])
    admin = forms.BooleanField(required=False)
    clinical = forms.BooleanField(required=False)


class PhoneReviewForm(forms.Form):
    account = forms.ModelChoiceField(queryset=Account.objects.filter(is_doctor=False))
    control = forms.ChoiceField(choices=[("private", "Personally controlled"), ("shared", "Shared")])


class RevokeForm(forms.Form):
    grant = forms.ModelChoiceField(queryset=AccessGrant.objects.filter(revoked_at__isnull=True))
