from django import forms

from accounts.services import normalize_phone


class PhoneForm(forms.Form):
    phone = forms.CharField(max_length=24, label="Indian mobile number")

    def clean_phone(self) -> str:
        return normalize_phone(self.cleaned_data["phone"])


class CodeForm(forms.Form):
    code = forms.CharField(max_length=6, min_length=6, widget=forms.TextInput(attrs={"autocomplete": "one-time-code"}))


class DoctorForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(widget=forms.PasswordInput)
    token = forms.CharField(max_length=16, label="Authenticator or recovery code")
    recovery = forms.BooleanField(required=False, label="Use a one-time recovery code")
