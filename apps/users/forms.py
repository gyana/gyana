from django import forms
from django.contrib.auth.forms import UserChangeForm

from .models import CustomUser


class CustomUserChangeForm(UserChangeForm):
    email = forms.EmailField(label="testing testing 123", required=True)

    class Meta:
        model = CustomUser
        fields = ["email", "first_name", "last_name"]
        labels = {"email": "Email"}


class UploadAvatarForm(forms.Form):
    avatar = forms.FileField()
