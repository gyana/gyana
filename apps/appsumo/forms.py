from allauth.account.forms import SignupForm
from django import forms

from .models import AppsumoCode


class AppsumoCodeForm(forms.ModelForm):
    class Meta:
        model = AppsumoCode
        fields = ["name"]


class AppsumoSignupForm(SignupForm):
    first_name = forms.CharField(max_length=30, label="Your Name")
    last_name = forms.CharField(max_length=30, label="Your Last Name")
    appsumo_code = forms.CharField(max_length=6)

    @property
    def field_order(self):
        return ["first_name", "last_name", "email", "password1", "appsumo_code"]
