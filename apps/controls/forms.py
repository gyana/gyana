from django import forms

from apps.base.forms import BaseLiveSchemaForm
from apps.base.widgets import DatetimeInput

from .models import Control, CustomChoice


class ControlForm(BaseLiveSchemaForm):
    class Meta:
        model = Control
        fields = ["date_range", "start", "end"]
        widgets = {
            "start": DatetimeInput(
                attrs={"class": "input--sm", "data-live-update-ignore": ""}
            ),
            "end": DatetimeInput(
                attrs={"class": "input--sm", "data-live-update-ignore": ""}
            ),
        }

    def get_live_fields(self):
        fields = ["date_range"]
        if self.get_live_field("date_range") == CustomChoice.CUSTOM:
            fields += ["start", "end"]
        return fields
