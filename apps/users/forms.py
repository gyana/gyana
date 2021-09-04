from allauth.account.forms import LoginForm
from django import forms
from django.contrib.auth.forms import UserChangeForm

from apps.base.analytics import identify_user

from .models import CustomUser


class UserOnboardingForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = [
            "company_industry",
            "company_role",
            "company_size",
        ]
        labels = {
            "company_industry": "What's your industry?",
            "company_role": "What's your role?",
            "company_size": "Company size",
        }

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.onboarded = True
        instance.save()

        return instance


class UserLoginForm(LoginForm):
    error_messages = {
        "account_inactive": "This account is currently inactive.",
        "email_password_mismatch": "The e-mail address and/or password you specified are not correct.",
        "username_password_mismatch": "The username and/or password you specified are not correct.",
        "username_email_password_mismatch": "The login and/or password you specified are not correct.",
    }

    # We already have labels, identical placeholders are pointless.
    def __init__(self, *args, **kwargs):
        super(UserLoginForm, self).__init__(*args, **kwargs)

        del self.fields["login"].widget.attrs["placeholder"]
        del self.fields["password"].widget.attrs["placeholder"]

    def login(self, *args, **kwargs):
        identify_user(self.user)

        return super(UserLoginForm, self).login(*args, **kwargs)


class CustomUserChangeForm(UserChangeForm):
    email = forms.EmailField(required=True, label="Email Address")
    password = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = CustomUser
        fields = ["email", "first_name", "last_name"]


class UploadAvatarForm(forms.Form):
    avatar = forms.FileField()
