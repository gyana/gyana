from django import forms
from django.urls import reverse
from django.utils.html import mark_safe

from apps.base.forms import BaseModelForm, LiveModelForm

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

        if access_field := self.fields.get("access"):
            access_field.required = False
            access_field.widget = forms.Select(
                choices=access_field.choices, attrs={"disabled": "disabled"}
            )
            access_field.help_text = (
                "Invite only projects are not available on your current plan"
            )


class ProjectCreateForm(MemberSelectMixin, LiveModelForm):
    class Meta:
        model = Project
        fields = ["name", "description", "access", "members"]
        widgets = {"members": MemberSelect()}

    def get_live_fields(self):
        fields = ["name", "description", "access"]

        if self.get_live_field("access") == Project.Access.INVITE_ONLY:
            fields += ["members"]

        return fields

    def pre_save(self, instance):
        instance.team = self._team


class ProjectUpdateForm(MemberSelectMixin, LiveModelForm):
    class Meta:
        model = Project
        fields = [
            "name",
            "description",
            "access",
            "members"
        ]
        widgets = {"members": MemberSelect()}

    def get_live_fields(self):
        fields = ["name", "description", "access"]

        if self.get_live_field("access") == Project.Access.INVITE_ONLY:
            fields += ["members"]

        return fields


class ProjectRunForm(BaseModelForm):
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
