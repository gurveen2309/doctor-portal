from django import forms


class ReplyForm(forms.Form):
    outcome = forms.ChoiceField(
        choices=[
            ("reply", "Reply"),
            ("missing_information", "Missing information"),
            ("consultation_required", "Consultation required"),
        ]
    )
    message = forms.CharField(widget=forms.Textarea)


class RepeatForm(forms.Form):
    outcome = forms.ChoiceField(
        choices=[("approve", "Approve"), ("decline", "Decline"), ("consultation_required", "Consultation required")]
    )


class VisitForm(forms.Form):
    follow_up_date = forms.DateField(required=False, widget=forms.DateInput(attrs={"type": "date"}))
    medicine = forms.CharField(required=False, widget=forms.Textarea)
    precautions = forms.CharField(required=False, widget=forms.Textarea)
    diet = forms.CharField(required=False, widget=forms.Textarea)
