from allauth.account.forms import SignupForm
from apps.base import analytics
from apps.base.forms import BaseModelForm
from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import AppsumoCode, AppsumoReview


class AppsumoCodeForm(forms.Form):
    code = forms.CharField(min_length=8, max_length=8, label="AppSumo code")

    def clean_code(self):
        code = self.cleaned_data["code"]

        if not AppsumoCode.code_exists(code):
            raise ValidationError("AppSumo code does not exist")

        if not AppsumoCode.code_available(code):
            raise ValidationError("AppSumo code is already redeemed")

        if AppsumoCode.code_refunded(code):
            raise ValidationError("AppSumo code has been refunded")

        return code


class AppsumoRedeemNewTeamForm(BaseModelForm):
    class Meta:
        model = AppsumoCode
        fields = []

    team_name = forms.CharField(
        max_length=100,
        label="Name your team",
        help_text="We recommend you use the name of your organisation, you can change it later",
    )

    def __init__(self, *args, **kwargs):
        self._user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

    def pre_save(self, instance):
        instance.redeem_new_team(self.cleaned_data["team_name"], self._user)


class AppsumoRedeemForm(BaseModelForm):
    class Meta:
        model = AppsumoCode
        fields = ["team"]

    def __init__(self, *args, **kwargs):
        self._user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        self.fields["team"].queryset = self._user.teams_admin_of
        self.fields["team"].widget.help_text = "You can always change this later"

    def pre_save(self, instance):
        instance.redeem_by_user(self._user)


class AppsumoSignupForm(SignupForm):
    team = forms.CharField(
        max_length=100,
        label="Team name",
        help_text="You can always change this name later.",
    )

    def __init__(self, *args, **kwargs):
        self._code = kwargs.pop("code", None)
        super().__init__(*args, **kwargs)

        del self.fields["email"].widget.attrs["placeholder"]
        del self.fields["password1"].widget.attrs["placeholder"]

        self.fields["email"].help_text = "e.g. maryjackson@nasa.gov"
        self.fields["password1"].help_text = "Must have at least 6 characters"

    @property
    def field_order(self):
        return [
            "email",
            "password1",
            "team",
        ]

    def save(self, request):
        with transaction.atomic():
            user = super().save(request)
            self._code.redeem_new_team(self.cleaned_data["team"], user)

        analytics.identify_user(user)
        return user


class AppsumoReviewForm(BaseModelForm):
    class Meta:
        model = AppsumoReview
        fields = ["review_link"]
        help_texts = {"review_link": "Paste a link to your review from Appsumo"}

    def __init__(self, *args, **kwargs):
        self._team = kwargs.pop("team", None)
        super().__init__(*args, **kwargs)

    def pre_save(self, instance):
        return instance.add_to_team(self._team)
