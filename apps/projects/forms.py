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


class ProjectUpdateForm(MemberSelectMixin, LiveModelForm):
    class Meta:
        model = Project
        fields = [
            "name",
            "description",
            "access",
            "members",
            "cname",
        ]
        widgets = {"members": MemberSelect()}
        labels = {"cname": "Custom domain"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if cname_field := self.fields.get("cname"):
            cname_field.empty_label = "Default domain (gyana.com)"
            cname_field.queryset = self._team.cname_set.all()

    def get_live_fields(self):
        fields = ["name", "description", "access", "cname"]

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

        if self.instance.team.is_free:
            daily_schedule_time.disabled = True
            daily_schedule_time.help_text = mark_safe(
                f'Scheduling is only available on a paid plan <a class="link" href="{reverse("teams:pricing", args=(self.instance.team.id, ))}" data-turbo-frame="_top">learn more</a>'
            )
        else:
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
