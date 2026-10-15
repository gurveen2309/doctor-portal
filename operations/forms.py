from django import forms

from operations.models import Charge, ReceiptEntry


class FulfillmentForm(forms.Form):
    status = forms.ChoiceField(
        choices=[
            ("preparing", "Preparing"),
            ("ready", "Ready"),
            ("dispatched", "Dispatched"),
            ("delivered", "Delivered / collected"),
            ("cancelled", "Cancel before preparation"),
        ]
    )
    carrier = forms.CharField(max_length=100, required=False)
    tracking_number = forms.CharField(max_length=100, required=False)
    tracking_link = forms.URLField(required=False, assume_scheme="https")


class ChargeForm(forms.Form):
    category = forms.ChoiceField(
        choices=[("consultation", "Consultation"), ("medicine", "Medicine"), ("delivery", "Delivery")]
    )
    amount = forms.DecimalField(min_value=0, max_digits=10, decimal_places=2)


class ReceiptForm(forms.Form):
    charge = forms.ModelChoiceField(queryset=Charge.objects.none())
    amount = forms.DecimalField(min_value=0, max_digits=10, decimal_places=2)
    method = forms.ChoiceField(choices=[("cash", "Cash received externally"), ("upi", "UPI received externally")])


class ChargeCorrectionForm(forms.Form):
    charge = forms.ModelChoiceField(queryset=Charge.objects.none())
    amount = forms.DecimalField(min_value=0, max_digits=10, decimal_places=2)


class ReceiptCorrectionForm(forms.Form):
    receipt = forms.ModelChoiceField(queryset=ReceiptEntry.objects.none())
    amount = forms.DecimalField(min_value=0, max_digits=10, decimal_places=2)
