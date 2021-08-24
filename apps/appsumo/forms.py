from allauth.account.forms import SignupForm
from apps.teams.models import Team
from django import forms
from django.db import transaction
from django.utils import timezone

from .models import AppsumoCode


class AppsumoCodeForm(forms.ModelForm):
    class Meta:
        model = AppsumoCode
        fields = ["code"]


class AppsumoRedeemForm(forms.ModelForm):
    class Meta:
        model = AppsumoCode
        fields = ["team"]

    def __init__(self, *args, **kwargs):
        user = kwargs.pop("user", None)
        super().__init__(*args, **kwargs)
        self.fields["team"].queryset = user.teams.all()

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.redeemed = timezone.now()

        if commit:
            with transaction.atomic():
                instance.save()
                self.save_m2m()

        return instance


class AppsumoSignupForm(SignupForm):
    first_name = forms.CharField(max_length=30, label="Your Name")
    last_name = forms.CharField(max_length=30, label="Your Last Name")
    team = forms.CharField(max_length=100)

    def __init__(self, *args, **kwargs):
        self._code = kwargs.pop("code", None)
        super().__init__(*args, **kwargs)

    @property
    def field_order(self):
        return [
            "first_name",
            "last_name",
            "email",
            "password1",
            "team",
        ]

    def save(self, request):
        with transaction.atomic():
            user = super().save(request)
            user.first_name = self.cleaned_data["first_name"]
            user.last_name = self.cleaned_data["last_name"]
            user.save()

            team = Team(name=self.cleaned_data["team"])
            team.save()
            team.members.add(user, through_defaults={"role": "admin"})

            appsumo_code = AppsumoCode.objects.get(code=self._code)
            appsumo_code.team = team
            appsumo_code.redeemed = timezone.now()
            appsumo_code.save()

        return user
