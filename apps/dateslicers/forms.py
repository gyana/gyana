from django import forms

from apps.base.widgets import DatetimeInput

from .models import DateSlicer


class DateSlicerForm(forms.ModelForm):
    class Meta:
        model = DateSlicer
        fields = ["start", "end"]
        widgets = {
            "start": DatetimeInput(
                attrs={"class": "input--sm", "onblur": "this.form.requestSubmit();"}
            ),
            "end": DatetimeInput(
                attrs={"class": "input--sm", "onblur": "this.form.requestSubmit();"}
            ),
        }
