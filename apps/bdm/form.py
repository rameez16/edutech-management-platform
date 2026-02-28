from django import forms
from django.db.models import Count
from django.contrib.auth import get_user_model
from apps.bdm.models import TrainerAdminProfile, Trainer,StudentAdminProfile ,Course ,Batch
from apps.trainer.models import Module ,LessonPlan

User = get_user_model()

class CreateUserForm(forms.ModelForm):
    
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={"placeholder": "••••••••"}),
        min_length=8,
        label="Password"
    )

    role = forms.ChoiceField(
        choices=[
            ("admin", "Admin"),
            ("trainer", "Trainer"),
            ("student", "Student"),
            ("counselor", "Counselor"),
            ("tele_caller", "Tele_Caller"),
        ],
        label="User Role"
    )

    is_active = forms.BooleanField(required=False, initial=True)
    is_staff = forms.BooleanField(required=False)
    is_superuser = forms.BooleanField(required=False)

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name","role"]

    def clean_username(self):
        username = self.cleaned_data["username"]
        if User.objects.filter(username=username).exists():
            raise forms.ValidationError("Username already exists")
        return username

    def clean_email(self):
        email = self.cleaned_data["email"]
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("Email already exists")
        return email

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.is_active = self.cleaned_data.get("is_active", True)
        user.is_staff = self.cleaned_data.get("is_staff", False)
        user.is_superuser = self.cleaned_data.get("is_superuser", False)        
        user.role = self.cleaned_data.get("role")

        

        if commit:
            user.save()
        return user

class TrainerAdminProfileForm(forms.ModelForm):

    class Meta:
        model = TrainerAdminProfile
        fields = [
            "salary",
            "performance_rating",
            "background_verified",
            "profile_verified",
            "is_active",
        ]



class StudentAdminProfileForm(forms.ModelForm):

    enrolled_course = forms.ModelChoiceField(
        queryset=Course.objects.all(),
        empty_label="Select Course (Optional)",
        required=False
    )

    batch_assigned = forms.ModelChoiceField(
        queryset=Batch.objects.annotate(
            student_count=Count("students")
        ),
        empty_label="Select Batch (Optional)",
        required=False
    )

    class Meta:
        model = StudentAdminProfile
        fields = [
            "enrolled_course",
            "batch_assigned",
            "booking_fee_paid",
            "background_verified",
            "profile_verified",
            "is_active",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["batch_assigned"].label_from_instance = (
            lambda batch: f"{batch.name} (Students: {batch.student_count})"
        )

from apps.trainer.models import LessonSession

class LessonSessionForm(forms.ModelForm):
    class Meta:
        model = LessonSession
        fields = [
            "planned_date",
            "trainer"
        ]
        widgets = {
            "planned_date": forms.DateInput(attrs={"type": "date"})
        }
        
class ModuleForm(forms.ModelForm):

    class Meta:
        model = Module
        fields = [
            'title',
            'description',
            'module_number',
            'total_sessions',
            'phase',
            'learning_objectives',
            'prerequisites'
        ]

        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'learning_objectives': forms.Textarea(attrs={'rows': 3}),
            'prerequisites': forms.Textarea(attrs={'rows': 2}),
        }
        

class LessonPlanForm(forms.ModelForm):
    class Meta:
        model = LessonPlan
        exclude = ['course', 'module']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 3}),
            'subtopics': forms.Textarea(attrs={'rows': 3}),
            'learning_outcomes': forms.Textarea(attrs={'rows': 3}),
            'reference_materials': forms.Textarea(attrs={'rows': 2}),
            'practice_exercises': forms.Textarea(attrs={'rows': 2}),
        }
