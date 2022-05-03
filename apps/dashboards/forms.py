import uuid

from django import forms
from django.core.exceptions import ValidationError
from django.core.validators import MaxValueValidator, MinValueValidator
from django.forms.widgets import HiddenInput, PasswordInput
from django.utils import timezone

from apps.base.fields import ColorField, ColorInput
from apps.base.forms import BaseModelForm, LiveModelForm

from .models import DASHBOARD_SETTING_TO_CATEGORY, Dashboard


class PaletteColorsWidget(forms.MultiWidget):
    widgets = [
        ColorInput(),
        ColorInput(),
        ColorInput(),
        ColorInput(),
        ColorInput(),
        ColorInput(),
        ColorInput(),
    ]

    def __init__(self, *args, **kwargs):
        super().__init__(widgets=self.widgets, *args, **kwargs)

    def decompress(self, value):
        if value:
            return value.split(" ")

        return [None]


class PaletteColorsField(forms.MultiValueField):
    widget = PaletteColorsWidget
    fields = (
        ColorField(),
        ColorField(),
        ColorField(),
        ColorField(),
        ColorField(),
        ColorField(),
        ColorField(),
    )

    def __init__(self, *args, **kwargs):
        super().__init__(
            fields=self.fields,
            *args,
            **kwargs,
        )

    def compress(self, data_list):
        return data_list

    def has_changed(self, initial, data):
        return super().has_changed(initial, map(lambda x: x.upper(), data))


class DashboardCreateForm(BaseModelForm):
    class Meta:
        model = Dashboard
        fields = ["project"]
        widgets = {"project": HiddenInput()}


class DashboardNameForm(BaseModelForm):
    class Meta:
        model = Dashboard
        fields = ["name"]


class DashboardForm(BaseModelForm):
    width = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(
            attrs={"class": "label--half", "unit_suffix": "pixels"}
        ),
    )
    height = forms.IntegerField(
        required=False,
        widget=forms.NumberInput(
            attrs={"class": "label--half", "unit_suffix": "pixels"}
        ),
    )
    grid_size = forms.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(1200)],
        required=False,
        widget=forms.NumberInput(attrs={"unit_suffix": "pixels"}),
    )
    palette_colors = PaletteColorsField(required=False)
    background_color = ColorField(required=False, initial="#ffffff")
    font_color = ColorField(required=False, initial="#6a6b77")
    font_size = forms.IntegerField(
        required=False,
        initial=14,
        widget=forms.NumberInput(
            attrs={"class": "label--third", "unit_suffix": "pixels"}
        ),
    )
    widget_header_font_size = forms.IntegerField(
        required=False,
        initial=18,
        widget=forms.NumberInput(
            attrs={"class": "label--third", "unit_suffix": "pixels"}
        ),
    )
    widget_background_color = ColorField(required=False, initial="#ffffff")
    widget_border_color = ColorField(required=False, initial="#e6e6e6")
    widget_border_radius = forms.IntegerField(
        required=False,
        initial=5,
        widget=forms.NumberInput(
            attrs={"class": "label--third", "unit_suffix": "pixels"}
        ),
    )
    widget_border_thickness = forms.IntegerField(
        required=False,
        initial=1,
        widget=forms.NumberInput(
            attrs={"class": "label--third", "unit_suffix": "pixels"}
        ),
    )

    class Meta:
        model = Dashboard
        fields = [
            "font_size",
            "font_family",
            "font_color",
            "background_color",
            "palette_colors",
            "width",
            "height",
            "grid_size",
            "snap_to_grid",
            "show_widget_border",
            "widget_header_font_size",
            "show_widget_headers",
            "widget_background_color",
            "widget_border_color",
            "widget_border_radius",
            "widget_border_thickness",
        ]
        labels = {"snap_to_grid": "Snap widgets to grid"}

    def __init__(self, *args, **kwargs):
        self.category = kwargs.pop("category")
        super().__init__(*args, **kwargs)

        self.fields["font_family"].widget.attrs.update({"class": "label--half"})

        for name, field in self.fields.items():
            if self.category != DASHBOARD_SETTING_TO_CATEGORY[name]:
                field.required = False

                # Fields that have initial values and multiple widgets will
                # error as a singular hidden input.
                if hasattr(field.widget, "widgets"):
                    field.widget = forms.MultipleHiddenInput()
                else:
                    field.widget = forms.HiddenInput()


class DashboardShareForm(LiveModelForm):
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


class DashboardVersionSaveForm(BaseModelForm):

    version_name = forms.CharField(required=False)

    class Meta:
        model = Dashboard
        fields = []

    def save(self, commit=True):
        self.instance.versions.create(name=self.cleaned_data["version_name"])
        return self.instance
