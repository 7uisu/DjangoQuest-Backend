# dashboard/forms.py
from django import forms
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from users.models import EducatorAccessCode

User = get_user_model()


class StudentRegistrationForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        label='In-Game Username',
        help_text='This will be your username inside the DjangoQuest game.',
        widget=forms.TextInput(attrs={
            'placeholder': 'Choose your in-game username',
            'autocomplete': 'username',
        }),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'you@example.com',
            'autocomplete': 'email',
        }),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Create a password',
            'autocomplete': 'new-password',
        }),
    )
    password_confirm = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirm your password',
            'autocomplete': 'new-password',
        }),
    )

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise ValidationError('This username is already taken.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError('An account with this email already exists.')
        return email

    def clean(self):
        cleaned_data = super().clean()
        pw = cleaned_data.get('password')
        pw2 = cleaned_data.get('password_confirm')
        if pw and pw2 and pw != pw2:
            self.add_error('password_confirm', 'Passwords do not match.')
        if pw:
            try:
                validate_password(pw)
            except ValidationError as e:
                self.add_error('password', e)
        return cleaned_data


class TeacherRegistrationForm(forms.Form):
    username = forms.CharField(
        max_length=150,
        label='Username',
        widget=forms.TextInput(attrs={
            'placeholder': 'Choose a username',
            'autocomplete': 'username',
        }),
    )
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'you@example.com',
            'autocomplete': 'email',
        }),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Create a password',
            'autocomplete': 'new-password',
        }),
    )
    password_confirm = forms.CharField(
        label='Confirm Password',
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Confirm your password',
            'autocomplete': 'new-password',
        }),
    )
    educator_access_code = forms.CharField(
        label='Educator Access Code',
        help_text='Enter the pre-issued educator access code (e.g. CAPSTONE-2026).',
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g. CAPSTONE-2026',
        }),
    )

    def clean_username(self):
        username = self.cleaned_data['username']
        if User.objects.filter(username=username).exists():
            raise ValidationError('This username is already taken.')
        return username

    def clean_email(self):
        email = self.cleaned_data['email']
        if User.objects.filter(email=email).exists():
            raise ValidationError('An account with this email already exists.')
        return email

    def clean_educator_access_code(self):
        code = self.cleaned_data['educator_access_code'].strip()
        if not EducatorAccessCode.objects.filter(code=code, is_active=True).exists():
            raise ValidationError('Invalid or expired Educator Access Code.')
        return code

    def clean(self):
        cleaned_data = super().clean()
        pw = cleaned_data.get('password')
        pw2 = cleaned_data.get('password_confirm')
        if pw and pw2 and pw != pw2:
            self.add_error('password_confirm', 'Passwords do not match.')
        if pw:
            try:
                validate_password(pw)
            except ValidationError as e:
                self.add_error('password', e)
        return cleaned_data


class UniversalLoginForm(forms.Form):
    email = forms.EmailField(
        widget=forms.EmailInput(attrs={
            'placeholder': 'you@example.com',
            'autocomplete': 'email',
        }),
    )
    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'placeholder': 'Enter your password',
            'autocomplete': 'current-password',
        }),
    )


class ClassroomForm(forms.Form):
    name = forms.CharField(
        max_length=200,
        label='Classroom Name',
        widget=forms.TextInput(attrs={
            'placeholder': 'e.g. CS101 - Spring 2026',
        }),
    )
