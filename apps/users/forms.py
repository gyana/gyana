from django import forms
from allauth.account.forms import LoginForm
from django.contrib.auth.forms import UserChangeForm

from .models import CustomUser

class UserLoginForm(LoginForm):
    error_messages = {
        'account_inactive': "This account is currently inactive.",
        'email_password_mismatch': "The e-mail address and/or password you specified are not correct.",
        'username_password_mismatch': "The username sdas dsad asd asd as and/or password you specified are not correct.",
        'username_email_password_mismatch': "The login ad asdsad asd asd asd as and/or password you specified are not correct."
    }

    def login(self, *args, **kwargs):
        return super(UserLoginForm, self).login(*args, **kwargs)

class CustomUserChangeForm(UserChangeForm):
    email = forms.EmailField(required=True)
    password = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = CustomUser
        fields = ["email", "first_name", "last_name"]


class UploadAvatarForm(forms.Form):
    avatar = forms.FileField()
