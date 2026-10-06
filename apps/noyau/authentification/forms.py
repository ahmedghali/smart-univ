# apps/noyau/authentification/forms.py

from django import forms
from django.contrib.auth.forms import AuthenticationForm
from .models import CustomUser


class LoginForm(forms.Form):
    """
    Formulaire de connexion personnalisé.
    """
    username = forms.CharField(
        max_length=150,
        required=True,
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'اسم المستخدم',
            'autocomplete': 'username',
        }),
        label='اسم المستخدم'
    )

    password = forms.CharField(
        required=True,
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'كلمة المرور',
            'autocomplete': 'current-password',
        }),
        label='كلمة المرور'
    )


class CustomAuthenticationForm(AuthenticationForm):
    """
    Formulaire d'authentification basé sur AuthenticationForm de Django.
    Alternative au LoginForm ci-dessus.
    """
    username = forms.CharField(
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'اسم المستخدم',
            'autocomplete': 'username',
        })
    )

    password = forms.CharField(
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'placeholder': 'كلمة المرور',
            'autocomplete': 'current-password',
        })
    )
