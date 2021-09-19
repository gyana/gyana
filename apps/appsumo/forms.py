import analytics
from allauth.account.forms import SignupForm
from apps.base.analytics import (
    APPSUMO_CODE_REDEEMED_EVENT,
    TEAM_CREATED_EVENT,
    identify_user,
)
from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction

from .models import AppsumoCode, AppsumoReview


class AppsumoCodeForm(forms.Form):
    code = forms.CharField(min_length=8, max_length=8, label="AppSumo code")

    def clean_code(self):
        code = self.cleaned_data["code"]

        if not AppsumoCode.exists(code):
            raise ValidationError("AppSumo code does not exist")

        if not AppsumoCode.available(code):
            raise ValidationError("AppSumo code is already redeemed")

        return code


class AppsumoRedeemNewTeamForm(forms.ModelForm):
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

    def save(self, commit=True):
        instance = super().save(commit=False)
        if commit == True:
            instance.redeem_new_team(self.cleaned_data["team_name"], self._user)

            analytics.track(self._user.id, APPSUMO_CODE_REDEEMED_EVENT)
            analytics.track(self._user.id, TEAM_CREATED_EVENT)
            # identify_user_group(self._user, team)

        return instance


class AppsumoRedeemForm(forms.ModelForm):
    class Meta:
        model = AppsumoCode
        fields = ["team"]

    def __init__(self, *args, **kwargs):
        self._user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)

        self.fields["team"].queryset = self._user.teams.all()
        self.fields["team"].widget.help_text = "You can always change this later"

    def save(self, commit=True):
        instance = super().save(commit=False)
        AppsumoCode.redeem_existing_team(
            instance, self.cleaned_data["team"], self._user
        )

        analytics.track(self._user.id, APPSUMO_CODE_REDEEMED_EVENT)

        return instance


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
            identify_user(user)

            AppsumoCode.redeem_existing_team(
                self._code, self.cleaned_data["team"], self._user
            )

        analytics.track(user.id, APPSUMO_CODE_REDEEMED_EVENT)
        analytics.track(user.id, TEAM_CREATED_EVENT)
        # identify_user_group(user, team)

        return user


class AppsumoReviewForm(forms.ModelForm):
    class Meta:
        model = AppsumoReview
        fields = ["review_link"]
        help_texts = {"review_link": "Paste a link to your review from Appsumo"}

    def __init__(self, *args, **kwargs):
        self._team = kwargs.pop("team", None)
        super().__init__(*args, **kwargs)

    def save(self, commit=True):
        with transaction.atomic():
            instance = super().save(commit=commit)
            instance.add_to_team(self._team)
