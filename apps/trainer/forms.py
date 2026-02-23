from django import forms
from apps.bdm.models import Trainer
from apps.trainer.models import Task, TaskSubmission, LessonSession, SessionMaterial
from django.utils import timezone 
from apps.bdm.models import StudentIssue
class TrainerProfileForm(forms.ModelForm):
    class Meta:
        model = Trainer
        fields = [

            'full_name', 'profile_photo', 'gender', 'email', 'phone', 'bio',
            'languages_spoken', 'location', 'timezone',

            'qualification', 'primary_domain', 'secondary_skills',
            'certifications', 'coding_languages', 'frameworks',
            'experience_years', 'teaching_experience_years', 'teaching_style',

            'portfolio_url', 'github_url', 'linkedin_url'
        ]
        widgets = {
            'bio': forms.Textarea(attrs={'rows': 4, 'placeholder': 'Tell something about yourself'}),
            'certifications': forms.Textarea(attrs={'rows': 3, 'placeholder': 'AWS, Google, Microsoft'}),
            'secondary_skills': forms.Textarea(attrs={'rows': 3, 'placeholder': 'DevOps, Cloud, AI'}),
            'languages_spoken': forms.TextInput(attrs={'placeholder': 'English, Hindi'}),
            'coding_languages': forms.TextInput(attrs={'placeholder': 'Python, JavaScript'}),
            'frameworks': forms.TextInput(attrs={'placeholder': 'Django, DRF'}),
            'experience_years': forms.NumberInput(attrs={'min': 0,'placeholder': 'Total industry experience'}),
            'teaching_experience_years': forms.NumberInput(attrs={'min': 0,'placeholder': 'Years of teaching experience'}),
        }


class TaskForm(forms.ModelForm):

    class Meta:
        model = Task
        fields = [
            "lesson_session",
            "title",
            "task_type",
            "difficulty_level",
            "description",
            "instructions",
            "reference_links",
            "attachment",
            "total_marks",
            "passing_marks",
            "due_date",
            "is_mandatory",
        ]

        widgets = {
            "due_date": forms.DateInput(attrs={"type": "date"}),
            "description": forms.Textarea(attrs={"rows": 3}),
            "instructions": forms.Textarea(attrs={"rows": 4}),
        }

    def clean(self):
        cleaned_data = super().clean()
        total = cleaned_data.get("total_marks")
        passing = cleaned_data.get("passing_marks")
        due = cleaned_data.get("due_date")

        if passing and total and passing > total:
            raise forms.ValidationError("Passing marks cannot exceed total marks.")

        if due and due < timezone.now().date():
            raise forms.ValidationError("Due date cannot be in the past.")

        return cleaned_data


class EvaluationForm(forms.ModelForm):
    class Meta:
        model = TaskSubmission
        fields = ["marks_obtained", "feedback"]

        widgets = {
            "feedback": forms.Textarea(attrs={"rows": 3}),
        }


class CompletedSessionForm(forms.ModelForm):
    class Meta:
        model = LessonSession
        fields = [
            'actual_date',
            'actual_duration_hours',
            'homework_assigned',
            'student_queries',
            'remarks',
        ]
        widgets = {
            'actual_date': forms.DateInput(attrs={'type': 'date','required': 'required'}),
            'homework_assigned': forms.Textarea(attrs={'rows':3, 'placeholder':'Homework details...'}),
            'student_queries': forms.Textarea(attrs={'rows':3, 'placeholder':'Student questions...'}),
            'remarks': forms.Textarea(attrs={'rows':3, 'placeholder':'Trainer remarks...'}),
        }
        
class SessionMaterialForm(forms.ModelForm):
    class Meta:
        model = SessionMaterial
        exclude = [
            'lesson_session',
            'uploaded_by',
            'upload_date',
            'file_size_mb',
            'view_count',
            'download_count',
            'created_at',
            'updated_at'
        ]
        
        
class TrainerIssueResolveForm(forms.ModelForm):
    class Meta:
        model = StudentIssue
        fields = [
            "resolution_notes",
        ]
        widgets = {
            "resolution_notes": forms.Textarea(
                attrs={
                    "class": "issues-detail-textarea-large",
                    "placeholder": "Enter resolution notes here..."
                }
            ),
        }