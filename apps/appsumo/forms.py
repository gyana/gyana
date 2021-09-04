import analytics
from allauth.account.forms import SignupForm
from apps.base.analytics import (
    APPSUMO_CODE_REDEEMED_EVENT,
    TEAM_CREATED_EVENT,
    identify_user,
)
from apps.teams.models import Team
from django import forms
from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import AppsumoCode, AppsumoReview


class AppsumoStackForm(forms.Form):
    code = forms.CharField(min_length=8, max_length=8)

    def clean_code(self):
        appsumo_code = AppsumoCode.objects.filter(
            code=self.cleaned_data["code"]
        ).first()

        if appsumo_code is None:
            raise ValidationError("AppSumo code does not exist")

        if appsumo_code.redeemed:
            raise ValidationError("AppSumo code is already redeemed")

        return appsumo_code


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
        instance.redeemed = timezone.now()
        instance.redeemed_by = self._user

        team = Team(name=self.cleaned_data["team_name"])
        instance.team = team

        if commit:
            with transaction.atomic():
                team.save()
                instance.save()
                self.save_m2m()
                team.members.add(self._user, through_defaults={"role": "admin"})

        analytics.track(self._user.id, APPSUMO_CODE_REDEEMED_EVENT)
        analytics.track(self._user.id, TEAM_CREATED_EVENT)

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
        instance.redeemed = timezone.now()
        instance.redeemed_by = self._user

        if commit:
            with transaction.atomic():
                instance.save()
                self.save_m2m()

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

            team = Team(name=self.cleaned_data["team"])
            team.save()
            team.members.add(user, through_defaults={"role": "admin"})

            appsumo_code = AppsumoCode.objects.get(code=self._code)
            appsumo_code.team = team
            appsumo_code.redeemed = timezone.now()
            appsumo_code.redeemed_by = user
            appsumo_code.save()

        analytics.track(user.id, APPSUMO_CODE_REDEEMED_EVENT)
        analytics.track(user.id, TEAM_CREATED_EVENT)

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
        instance = super().save(commit=False)
        instance.team = self._team

        if commit:
            with transaction.atomic():
                instance.save()
                self.save_m2m()
