from django import forms
from django.contrib.auth.forms import UserCreationForm
from django.core.exceptions import ValidationError
from .models import User, Member, Profile, Campus

class UserRegistrationForm(forms.Form):
    full_name = forms.CharField(
        max_length=150,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'John Doe'
        })
    )
    
    email = forms.EmailField(
        max_length=254,
        widget=forms.EmailInput(attrs={
            'class': 'form-control',
            'placeholder': 'your.email@example.com'
        })
    )
    
    batch = forms.CharField(
        max_length=10,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., 2020 or 2020-2024'
        })
    )
    
    course = forms.CharField(
        max_length=100,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., Computer Science'
        })
    )
    
    phone = forms.CharField(
        max_length=20,
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., +1234567890'
        })
    )
    
    graduation_year = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': 'e.g., 2024',
            'min': '1900',
            'max': '2100'
        })
    )

    def clean_email(self):
        email = self.cleaned_data.get('email')
        if Member.objects.filter(email=email).exists():
            raise ValidationError("A member with this email already exists.")
        return email

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

class ProfileRegistrationForm(forms.ModelForm):
    campus = forms.ModelChoiceField(
        queryset=Campus.objects.filter(is_active=True),
        required=False,
        empty_label="Select Campus",
        widget=forms.Select(attrs={'class': 'form-control'})
    )
    
    gender = forms.ChoiceField(
        choices=Profile.GENDER_CHOICES,
        widget=forms.RadioSelect(),
        initial='P',
        required=True
    )

    class Meta:
        model = Profile
        fields = ['gender', 'campus', 'bio', 'photo']
        widgets = {
            'bio': forms.Textarea(attrs={
                'class': 'form-control',
                'placeholder': 'Tell us about yourself...',
                'rows': 4
            }),
            'photo': forms.FileInput(attrs={
                'class': 'form-control',
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['gender'].widget.attrs.update({'class': 'form-check-input'})

class MemberUpdateForm(forms.ModelForm):
    class Meta:
        model = Member
        fields = ['full_name', 'email', 'batch', 'course', 'phone', 'graduation_year',
                  'address', 'current_job', 'current_company',
                  'linkedin_url', 'github_url', 'portfolio_url']
        widgets = {
            'full_name': forms.TextInput(attrs={'class': 'form-control'}),
            'email': forms.EmailInput(attrs={'class': 'form-control'}),
            'batch': forms.TextInput(attrs={'class': 'form-control'}),
            'course': forms.TextInput(attrs={'class': 'form-control'}),
            'phone': forms.TextInput(attrs={'class': 'form-control'}),
            'graduation_year': forms.NumberInput(attrs={'class': 'form-control'}),
            'address': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'current_job': forms.TextInput(attrs={'class': 'form-control'}),
            'current_company': forms.TextInput(attrs={'class': 'form-control'}),
            'linkedin_url': forms.URLInput(attrs={'class': 'form-control'}),
            'github_url': forms.URLInput(attrs={'class': 'form-control'}),
            'portfolio_url': forms.URLInput(attrs={'class': 'form-control'}),
        }
    
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

class UserUpdateForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['is_active', 'is_verified']
        widgets = {
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'is_verified': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }