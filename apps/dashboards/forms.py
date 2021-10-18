import uuid

from apps.base.live_update_form import LiveUpdateForm
from django import forms
from django.core.exceptions import ValidationError
from django.forms.widgets import HiddenInput, PasswordInput
from django.utils import timezone

from .models import Dashboard


class DashboardCreateForm(forms.ModelForm):
    class Meta:
        model = Dashboard
        fields = ["project"]
        widgets = {"project": HiddenInput()}


class DashboardForm(forms.ModelForm):
    name = forms.CharField(required=False)
    width = forms.IntegerField(required=False)
    height = forms.IntegerField(required=False)

    class Meta:
        model = Dashboard
        fields = ["name", "width", "height"]


class DashboardShareForm(LiveUpdateForm):
    class Meta:
        model = Dashboard
        fields = ["shared_status", "password"]
        widgets = {"password": PasswordInput(attrs={"autocomplete": "one-time-code"})}

    def __init__(self, *args, **kwargs):
        is_beta = kwargs.pop("is_beta")

        super().__init__(*args, **kwargs)
        self.fields["shared_status"].choices = [
            choice
            for choice in self.fields["shared_status"].choices
            if (choice[0] != Dashboard.SharedStatus.PASSWORD_PROTECTED or is_beta)
        ]

    def get_live_fields(self):
        fields = ["shared_status"]

        if (
            self.get_live_field("shared_status")
            == Dashboard.SharedStatus.PASSWORD_PROTECTED
        ):
            fields += ["password"]
        return fields

    def save(self, commit=True):
        dashboard = super().save(commit=False)

        if (
            dashboard.shared_status != Dashboard.SharedStatus.PRIVATE
            and dashboard.shared_id is None
        ):
            dashboard.shared_id = uuid.uuid4()

        if (
            self.get_live_field("shared_status")
            == Dashboard.SharedStatus.PASSWORD_PROTECTED
        ) and self.get_live_field("password"):
            dashboard.set_password(self.cleaned_data["password"])
            dashboard.password_set = timezone.now()
        if commit:
            dashboard.save()

        return dashboard


class DashboardLoginForm(forms.Form):
    password = forms.CharField(widget=forms.PasswordInput())

    def __init__(self, *args, **kwargs):
        self._dashboard = kwargs.pop("dashboard")
        super().__init__(*args, **kwargs)

    def clean_password(self):
        password = self.cleaned_data["password"]

        if not self._dashboard.check_password(password):
            raise ValidationError("Wrong password")

        return password
