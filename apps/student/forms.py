from django import forms
from apps.student.models import EnrollmentAgreement,LeaveApplication
from django.core.exceptions import ValidationError
from django.utils import timezone
from apps.trainer.models import Task,TaskSubmission

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






class LeaveApplicationForm(forms.ModelForm):

    class Meta:
        model = LeaveApplication
        fields = [
            'leave_type',
            'from_date',
            'to_date',
            'reason',
            'supporting_document'
        ]

        widgets = {
            'leave_type': forms.Select(attrs={
                'class': 'input'
            }),

            'from_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'input',
                'id': 'from_date'
            }),

            'to_date': forms.DateInput(attrs={
                'type': 'date',
                'class': 'input',
                'id': 'to_date'
            }),

            'reason': forms.Textarea(attrs={
                'class': 'input',
                'rows': 3,
                'placeholder': 'Enter leave reason...'
            }),

            'supporting_document': forms.FileInput(attrs={
                'class': 'input'
            }),
        }

    # ✅ DATE VALIDATION 🔥🔥🔥
    def clean(self):

        cleaned_data = super().clean()

        from_date = cleaned_data.get("from_date")
        to_date = cleaned_data.get("to_date")

        if from_date and to_date:

            if to_date < from_date:
                raise ValidationError("To Date cannot be earlier than From Date 🚨")

        return cleaned_data





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
