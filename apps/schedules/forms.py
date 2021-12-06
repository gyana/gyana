from django import forms

from apps.base.forms import BaseModelForm

from .models import Schedule


class ScheduleSettingsForm(BaseModelForm):
    class Meta:
        model = Schedule
        fields = [
            "daily_schedule_time",
        ]
        widgets = {
            "daily_schedule_time": forms.TimeInput(attrs={"step": "3600"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if daily_schedule_time_field := self.fields.get("daily_schedule_time"):
            daily_schedule_time_field.help_text = f"Select an hour in {self.instance.project.team.timezone_with_gtm_offset}"

    def pre_save(self, instance):
        self._daily_schedule_time_is_dirty = (
            "daily_schedule_time" in instance.get_dirty_fields()
        )

    def post_save(self, instance):
        if self._daily_schedule_time_is_dirty:
            instance.update_daily_sync_time()
