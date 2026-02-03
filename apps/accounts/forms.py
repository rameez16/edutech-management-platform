from django import forms
from accounts.models import User

class TrainerStudentUserCreationForm(forms.ModelForm):
    
    password = forms.CharField(
        widget=forms.PasswordInput,
        help_text="Temporary password"
    )

    role = forms.ChoiceField(choices=[
        ("trainer", "Trainer"),
        ("student", "Student"),
    ])

    class Meta:
        model = User
        fields = [
            "username",
            "first_name",
            "last_name",
            "email",
            "role",
            "password"
        ]

    def save(self, commit=True):
        user = super().save(commit=False)
        user.set_password(self.cleaned_data["password"])
        user.is_active = True

        if commit:
            user.save()

        return user