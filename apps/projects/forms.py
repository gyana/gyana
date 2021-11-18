from django import forms

from apps.base.live_update_form import LiveUpdateForm

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

        if not self._team.can_create_invite_only_project and (
            access_field := self.fields.get("access")
        ):
            access_field.required = False
            access_field.widget = forms.Select(
                choices=access_field.choices, attrs={"disabled": "disabled"}
            )
            access_field.help_text = (
                "Invite only projects are not available on your current plan"
            )


class ProjectCreateForm(MemberSelectMixin, LiveUpdateForm):
    class Meta:
        model = Project
        fields = ["name", "description", "access", "members"]
        widgets = {"members": MemberSelect()}

    def get_live_fields(self):
        fields = ["name", "description", "access"]

        if self.get_live_field("access") == Project.Access.INVITE_ONLY:
            fields += ["members"]

        return fields

    def clean(self):
        cleaned_data = super().clean()

        if not self._team.can_create_project:
            raise forms.ValidationError(
                "You've reached the maximum number of projects on this plan"
            )

        if (
            cleaned_data.get("access", False)
            and cleaned_data["access"] == Project.Access.INVITE_ONLY
            and not self._team.can_create_invite_only_project
        ):
            raise forms.ValidationError(
                "You've reached the maximum number of invite only projects on your plan"
            )

        return cleaned_data

    def pre_save(self, instance):
        instance.team = self._team


class ProjectUpdateForm(MemberSelectMixin, LiveUpdateForm):
    class Meta:
        model = Project
        fields = [
            "name",
            "description",
            "access",
            "members",
            "cname",
            "daily_schedule_time",
        ]
        widgets = {
            "members": MemberSelect(),
            "daily_schedule_time": forms.TimeInput(attrs={"step": "3600"}),
        }
        labels = {"cname": "Custom domain"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if cname_field := self.fields.get("cname"):
            cname_field.empty_label = "Default domain (gyana.com)"
            cname_field.queryset = self._team.cname_set.all()

        if daily_schedule_time_field := self.fields.get("daily_schedule_time"):
            daily_schedule_time_field.help_text = (
                f"Select an hour in {self._team.timezone_with_gtm_offset}"
            )

    def get_live_fields(self):
        fields = ["name", "description", "access", "cname", "daily_schedule_time"]

        if self.get_live_field("access") == Project.Access.INVITE_ONLY:
            fields += ["members"]

        return fields

    def pre_save(self, instance):
        self._daily_schedule_time_is_dirty = (
            "daily_schedule_time" in instance.get_dirty_fields()
        )

    def post_save(self, instance):
        if self._daily_schedule_time_is_dirty:
            instance.update_connectors_daily_sync_time()
