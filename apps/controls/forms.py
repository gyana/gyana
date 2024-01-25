from apps.base.forms import ModelForm
from apps.base.widgets import DatetimeInput

from .models import Control, CustomChoice


class ControlForm(ModelForm):
    class Meta:
        model = Control
        fields = ["date_range", "start", "end"]
        widgets = {
            "start": DatetimeInput(attrs={"class": "input--sm"}),
            "end": DatetimeInput(attrs={"class": "input--sm"}),
        }
        show = {
            "start": f"date_range === '{CustomChoice.CUSTOM}'",
            "end": f"date_range === '{CustomChoice.CUSTOM}'",
        }
