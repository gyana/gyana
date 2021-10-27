from apps.base.live_update_form import LiveUpdateForm
from django import forms

from .models import Project
from .widgets import MemberSelect


class ProjectForm(LiveUpdateForm):
    class Meta:
        model = Project
        fields = ["name", "description", "access", "members", "cname"]
        widgets = {"members": MemberSelect()}
        labels = {"cname": "CNAME"}

    def __init__(self, current_user, *args, **kwargs):
        self._team = kwargs.pop("team", None)
        self._is_beta = kwargs.pop("is_beta")
        super().__init__(*args, **kwargs)

        if members_field := self.fields.get("members"):
            members_field.queryset = self._team.members.all()
            members_field.widget.current_user = current_user

        if cname_field := self.fields.get("cname"):
            cname_field.empty_label = "No CNAME (gyana.com)"
            cname_field.queryset = self._team.cname_set.all()

    def get_live_fields(self):
        fields = ["name", "description"]

        if self._is_beta:
            fields += ["access", "cname"]

        if self.get_live_field("access") == Project.Access.INVITE_ONLY:
            fields += ["members"]

        return fields

    def pre_save(self, instance):
        instance.team = self._team


class ProjectCreateForm(ProjectForm):
    def get_live_fields(self):
        fields = ["name", "description"]

        if self._is_beta:
            fields += ["access"]

        if self.get_live_field("access") == Project.Access.INVITE_ONLY:
            fields += ["members"]

        return fields

    def clean(self):
        cleaned_data = super().clean()

        if not self._team.can_create_project:
            raise forms.ValidationError(
                "You've reached the maximum number of projects on this plan"
            )

        return cleaned_data
