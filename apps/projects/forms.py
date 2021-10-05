from apps.base.live_update_form import LiveUpdateForm
from django import forms

from .models import Project
from .widgets import MemberSelect


class ProjectForm(LiveUpdateForm):
    class Meta:
        model = Project
        fields = ["name", "description", "access", "members"]
        widgets = {"members": MemberSelect()}

    def __init__(self, current_user, *args, **kwargs):
        self._team = kwargs.pop("team", None)
        self._is_beta = kwargs.pop("is_beta")
        super().__init__(*args, **kwargs)

        if members_field := self.fields.get("members"):
            members_field.queryset = self._team.members.all()
            members_field.widget.current_user = current_user

    def get_live_fields(self):
        if not (self._is_beta and self._team.plan.get("sub_accounts") is not None):
            return ["name", "description"]
        fields = ["name", "description", "access"]
        if self.get_live_field("access") == Project.Access.INVITE_ONLY:
            fields += ["members"]
        return fields

    def on_save(self, instance):
        instance.team = self._team


class ProjectCreateForm(ProjectForm):
    def clean(self):
        cleaned_data = super().clean()

        if not self._team.can_create_project:
            raise forms.ValidationError(
                "You've reached the maximum number of projects on this plan"
            )

        return cleaned_data
