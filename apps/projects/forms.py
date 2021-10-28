from apps.base.live_update_form import LiveUpdateForm
from apps.base.widgets import SelectWithDisable
from django import forms

from .models import Project
from .widgets import MemberSelect


class ProjectForm(LiveUpdateForm):
    class Meta:
        model = Project
        fields = ["name", "description", "access", "members", "cname"]
        widgets = {"members": MemberSelect()}
        labels = {"cname": "Custom domain"}

    def __init__(self, current_user, *args, **kwargs):
        self._team = kwargs.pop("team", None)
        super().__init__(*args, **kwargs)

        if members_field := self.fields.get("members"):
            members_field.queryset = self._team.members.all()
            members_field.widget.current_user = current_user

        if cname_field := self.fields.get("cname"):
            cname_field.empty_label = "Default domain (gyana.com)"
            cname_field.queryset = self._team.cname_set.all()

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

    def get_live_fields(self):
        fields = ["name", "description", "access", "cname"]

        if self.get_live_field("access") == Project.Access.INVITE_ONLY:
            fields += ["members"]

        return fields

    def pre_save(self, instance):
        instance.team = self._team


class ProjectCreateForm(ProjectForm):
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
