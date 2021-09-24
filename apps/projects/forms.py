from apps.base.live_update_form import LiveUpdateForm
from apps.teams.models import Team
from django import forms
from django.forms.widgets import HiddenInput
from django.shortcuts import get_object_or_404

from .models import Project
from .widgets import MemberSelect


class ProjectForm(LiveUpdateForm):
    class Meta:
        model = Project
        fields = ["name", "description", "team", "access", "members"]
        widgets = {"team": HiddenInput(), "members": MemberSelect()}

    def __init__(self, current_user, *args, **kwargs):
        super().__init__(*args, **kwargs)

        if members_field := self.fields.get("members"):
            team = get_object_or_404(Team, pk=self.get_live_field("team"))
            members_field.queryset = team.members.all()
            members_field.widget.current_user = current_user

    def get_live_fields(self):
        fields = ["name", "description", "team", "access"]
        if self.get_live_field("access") == Project.Access.INVITE_ONLY:
            fields += ["members"]
        return fields
