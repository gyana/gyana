import uuid

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.forms.widgets import HiddenInput, PasswordInput
from django.utils import timezone

from apps.base.live_update_form import LiveUpdateForm

from .models import Dashboard


class PaletteColorsWidget(forms.MultiWidget):
    def __init__(self, *args, **kwargs):
        super(PaletteColorsWidget, self).__init__(
            [
                forms.TextInput(attrs={"type": "color"}),
                forms.TextInput(attrs={"type": "color"}),
                forms.TextInput(attrs={"type": "color"}),
                forms.TextInput(attrs={"type": "color"}),
                forms.TextInput(attrs={"type": "color"}),
                forms.TextInput(attrs={"type": "color"}),
                forms.TextInput(attrs={"type": "color"}),
                forms.TextInput(attrs={"type": "color"}),
                forms.TextInput(attrs={"type": "color"}),
                forms.TextInput(attrs={"type": "color"}),
            ],
            *args,
            **kwargs
        )

    def decompress(self, value):
        if value:
            return value.split(" ")

        return [None]


class PaletteColorsField(forms.MultiValueField):
    widget = PaletteColorsWidget

    def __init__(self, *args, **kwargs):
        super(PaletteColorsField, self).__init__(
            (
                forms.CharField(),
                forms.CharField(),
                forms.CharField(),
                forms.CharField(),
                forms.CharField(),
                forms.CharField(),
                forms.CharField(),
                forms.CharField(),
                forms.CharField(),
                forms.CharField(),
            ),
            *args,
            **kwargs
        )

    def compress(self, data_list):
        return data_list


class DashboardCreateForm(forms.ModelForm):
    class Meta:
        model = Dashboard
        fields = ["project"]
        widgets = {"project": HiddenInput()}


class DashboardNameForm(forms.ModelForm):
    class Meta:
        model = Dashboard
        fields = ["name"]


class DashboardForm(forms.ModelForm):
    width = forms.IntegerField(
        required=False, widget=forms.NumberInput(attrs={"step": "15"})
    )
    height = forms.IntegerField(
        required=False, widget=forms.NumberInput(attrs={"step": "15"})
    )
    grid_size = forms.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(1200)], required=False
    )
    palette_colors = PaletteColorsField(required=False)
    background_color = forms.CharField(
        help_text="Color to use for the background of the dashboard",
        required=False,
        widget=forms.TextInput(attrs={"type": "color"}),
    )

    class Meta:
        model = Dashboard
        fields = [
            "background_color",
            "palette_colors",
            "width",
            "height",
            "grid_size",
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["width"].widget.attrs.update({"step": self.instance.grid_size})
        self.fields["height"].widget.attrs.update({"step": self.instance.grid_size})

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
