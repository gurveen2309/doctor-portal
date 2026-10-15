from django import forms


class RequestForm(forms.Form):
    kind = forms.ChoiceField(
        choices=[
            ("appointment", "Appointment"),
            ("clarification", "Clinical clarification"),
            ("repeat", "Repeat medicine"),
        ]
    )
    idempotency_key = forms.CharField(max_length=64, widget=forms.HiddenInput)
    starts_at = forms.DateTimeField(required=False, widget=forms.DateTimeInput(attrs={"type": "datetime-local"}))
    ends_at = forms.DateTimeField(required=False, widget=forms.DateTimeInput(attrs={"type": "datetime-local"}))
    time_sensitive = forms.BooleanField(required=False)
    reason = forms.CharField(
        required=False, widget=forms.Textarea(attrs={"rows": 2}), label="Private time-sensitive reason"
    )
    message = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 3}), label="Private request details")
    preference = forms.ChoiceField(choices=[("pickup", "Pickup"), ("delivery", "Delivery")])
    delivery_address = forms.CharField(max_length=300, required=False, label="Minimum address, only for delivery")


class IntervalForm(forms.Form):
    starts_at = forms.DateTimeField(widget=forms.DateTimeInput(attrs={"type": "datetime-local"}))
    ends_at = forms.DateTimeField(widget=forms.DateTimeInput(attrs={"type": "datetime-local"}))


class InformationForm(forms.Form):
    message = forms.CharField(widget=forms.Textarea)


class PriorityForm(forms.Form):
    priority = forms.TypedChoiceField(coerce=int, choices=[(0, "Routine"), (1, "Elevated"), (2, "First")])
