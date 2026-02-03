from django import forms
from django.contrib.auth import get_user_model
from apps.bdm.models import TrainerAdminProfile, Trainer,StudentAdminProfile

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
            ("tele_caller", "Tele Caller"),
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
            "trainer",
            "salary",
            "batches_assigned",
            "performance_rating",
            "background_verified",
            "profile_verified",
            "is_active",
        ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Show only trainers without admin profile (optional but recommended)
        self.fields["trainer"].queryset = Trainer.objects.filter(
            admin_profile__isnull=True
        )


class StudentAdminProfileForm(forms.ModelForm):

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

        widgets = {
            "booking_fee_paid": forms.NumberInput(
                attrs={"placeholder": "Booking fee paid"}
            ),
        }
        