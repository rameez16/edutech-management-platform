from django import forms
from apps.student.models import EnrollmentAgreement
from apps.trainer.models import TaskSubmission

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





class TaskSubmissionForm(forms.ModelForm):
    class Meta:
        model = TaskSubmission
        fields = [
            "submission_text",
            "submission_file",
            "submission_link",
        ]

        widgets = {
            "submission_text": forms.Textarea(attrs={
                "rows": 5,
                "class": "form-control",
                "placeholder": "Describe your work..."
            }),
            "submission_link": forms.URLInput(attrs={
                "class": "form-control",
                "placeholder": "GitHub / Live Project URL"
            }),
        }