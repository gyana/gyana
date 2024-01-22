from django import forms

from apps.base.forms import ModelForm

from .models import Project
from .widgets import MemberSelect


class MemberSelectMixin:
    def __init__(self, *args, **kwargs):
        self._team = kwargs.pop("team", None)
        current_user = kwargs.pop("current_user", None)
        super().__init__(*args, **kwargs)

        if members_field := self.fields.get("members"):
            members_field.queryset = self._team.members.all()
            members_field.widget.current_user = current_user


class ProjectCreateForm(MemberSelectMixin, ModelForm):
    class Meta:
        model = Project
        fields = ["name", "description", "access", "members"]
        show = {"members": f'access == "{Project.Access.INVITE_ONLY}"'}
        widgets = {"members": MemberSelect()}

    def pre_save(self, instance):
        instance.team = self._team


class ProjectUpdateForm(MemberSelectMixin, ModelForm):
    class Meta:
        model = Project
        fields = ["name", "description", "access", "members"]
        show = {"members": f'access == "{Project.Access.INVITE_ONLY}"'}
        widgets = {"members": MemberSelect()}


class ProjectRunForm(ModelForm):
    class Meta:
        model = Project
        fields = [
            "daily_schedule_time",
        ]
        widgets = {
            "daily_schedule_time": forms.TimeInput(attrs={"step": "3600"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        daily_schedule_time = self.fields["daily_schedule_time"]
        daily_schedule_time.help_text = (
            f"Select an hour in {self.instance.team.timezone_with_gtm_offset}"
        )

    def pre_save(self, instance):
        self._daily_schedule_time_is_dirty = (
            "daily_schedule_time" in instance.get_dirty_fields()
        )

    def post_save(self, instance):
        if self._daily_schedule_time_is_dirty:
            instance.update_schedule()
