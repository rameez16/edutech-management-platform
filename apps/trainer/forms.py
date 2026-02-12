from django import forms
from apps.bdm.models import Trainer

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
