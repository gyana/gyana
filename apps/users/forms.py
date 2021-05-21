from django import forms
from django.contrib.auth.forms import UserChangeForm

from .models import CustomUser


class CustomUserChangeForm(UserChangeForm):
    email = forms.EmailField(required=True)
    password = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = CustomUser
        fields = ["email", "first_name", "last_name"]


class UploadAvatarForm(forms.Form):
    avatar = forms.FileField()
