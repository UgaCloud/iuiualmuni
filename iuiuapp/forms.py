from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import User, Profile, Campus


class UserRegistrationForm(UserCreationForm):
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your.email@example.com'
        })
    )
    full_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'John Doe'
        })
    )

    class Meta:
        model = User
        fields = ['email', 'full_name', 'password1', 'password2']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['password1'].widget.attrs.update({'class': 'form-control'})
        self.fields['password2'].widget.attrs.update({'class': 'form-control'})

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if User.objects.filter(email=email).exists():
            raise ValidationError("A user with this email already exists.")
        return email


class ProfileRegistrationForm(forms.ModelForm):
    campus = forms.ModelChoiceField(
        queryset=Campus.objects.filter(is_active=True),
        required=False,
        empty_label="Select Campus",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    # Add gender field to form
    gender = forms.ChoiceField(
        choices=Profile.GENDER_CHOICES,
        widget=forms.RadioSelect(),
        initial='P',
        required=True
    )

    class Meta:
        model = Profile
        fields = ['gender', 'batch', 'course', 'campus', 'phone', 'graduation_year']
        widgets = {
            'batch': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 2020 or 2020-2024'
            }),
            'course': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., Computer Science'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., +1234567890'
            }),
            'graduation_year': forms.NumberInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 2024',
                'min': '1900',
                'max': '2100'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Style radio buttons for Bootstrap
        self.fields['gender'].widget.attrs.update({'class': 'form-check-input'})

    def clean_batch(self):
        batch = self.cleaned_data.get('batch')
        if batch and not batch.replace('-', '').isdigit():
            raise ValidationError("Batch must contain only numbers and hyphens.")
        return batch

    def clean_graduation_year(self):
        year = self.cleaned_data.get('graduation_year')
        if year and (year < 1900 or year > 2100):
            raise ValidationError("Please enter a valid graduation year.")
        return year




