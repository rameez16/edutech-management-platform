from django import forms
from apps.student.models import EnrollmentAgreement

class EnrollmentAgreementForm(forms.ModelForm):
    class Meta:
        model = EnrollmentAgreement
        fields = ["payment_plan", "agreement_file", "is_signed"]

        widgets = {
            "payment_plan": forms.Select(attrs={
                "class": "form-select",
                "style": "width:80%; height:35px;"
            }),
            "agreement_file": forms.FileInput(attrs={
                "class": "form-control"
            }),
            "is_signed": forms.CheckboxInput(attrs={
                "class": "form-check-input"
            }),
        }