from apps.base.live_update_form import LiveUpdateForm
from django import forms
from django.forms.widgets import HiddenInput, PasswordInput

from .models import Dashboard


class DashboardFormCreate(forms.ModelForm):
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

    def get_live_fields(self):
        fields = ["shared_status"]

        if (
            self.get_live_field("shared_status")
            == Dashboard.SharedStatus.PASSWORD_PROTECTED
        ):
            fields += ["password"]
        return fields

    def save(self, commit=True):
        user = super().save(commit=False)
        if (
            self.get_live_field("shared_status")
            == Dashboard.SharedStatus.PASSWORD_PROTECTED
        ) and self.get_live_field("password"):
            user.set_password(self.cleaned_data["password"])
        if commit:
            user.save()
        return user
