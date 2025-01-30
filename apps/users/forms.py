from allauth.account.forms import LoginForm
from django import forms
from django.contrib.auth.forms import UserChangeForm

from apps.base.forms import ModelForm

from .models import CustomUser


class UserNameForm(ModelForm):
    first_name = forms.CharField(
        required=True, widget=forms.TextInput(attrs={"class": "label--half"})
    )
    last_name = forms.CharField(widget=forms.TextInput(attrs={"class": "label--half"}))

    class Meta:
        model = CustomUser
        fields = ["first_name", "last_name"]

    def pre_save(self, instance):
        instance.onboarded = True


class UserLoginForm(LoginForm):
    template_name = "django/forms/default_form.html"

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


class CustomUserChangeForm(ModelForm, UserChangeForm):
    email = forms.EmailField(required=True, label="Email Address")
    password = forms.CharField(widget=forms.HiddenInput(), required=False)
    marketing_allowed = forms.TypedChoiceField(
        coerce=lambda x: x == "True",
        choices=((True, "Yes"), (False, "No")),
        label="Opt-in to email communications",
        help_text="Allow us to email you with content relevant to the app",
        widget=forms.RadioSelect,
    )

    class Meta:
        model = CustomUser
        fields = ["avatar", "email", "first_name", "last_name", "marketing_allowed"]
        widgets = {
            "first_name": forms.TextInput(attrs={"class": "label--half"}),
            "last_name": forms.TextInput(attrs={"class": "label--half"}),
            "avatar": forms.ClearableFileInput(attrs={"accept": "image/*"}),
        }
        labels = {
            "first_name": "First Name",
            "last_name": "Last Name",
        }
        help_texts = {
            "email": "Changing this will not change the email you use to login",
            "first_name": "We use this name to help personalize content and support",
        }

    def pre_save(self, instance):
        self.instance.avatar = self.files.get("avatar", instance.avatar)
