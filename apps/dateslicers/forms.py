from django import forms

from apps.base.live_update_form import LiveUpdateForm
from apps.base.widgets import DatetimeInput

from .models import CustomChoice, DateSlicer


class DateSlicerForm(LiveUpdateForm):
    class Meta:
        model = DateSlicer
        fields = ["date_range", "start", "end"]
        widgets = {
            "start": DatetimeInput(
                attrs={
                    "class": "input--sm",
                }
            ),
            "end": DatetimeInput(
                attrs={
                    "class": "input--sm",
                }
            ),
        }

    def get_live_fields(self):
        fields = ["date_range"]
        if self.get_live_field("date_range") == CustomChoice.CUSTOM:
            fields += ["start", "end"]
        return fields
