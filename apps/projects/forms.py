from apps.base.live_update_form import LiveUpdateForm
from django.db import transaction

from .models import Project
from .widgets import MemberSelect


class ProjectForm(LiveUpdateForm):
    class Meta:
        model = Project
        fields = ["name", "description", "team", "access", "members"]
        widgets = {"members": MemberSelect()}

    def __init__(self, current_user, *args, **kwargs):
        self._team = kwargs.pop("team", None)
        super().__init__(*args, **kwargs)

        if members_field := self.fields.get("members"):
            members_field.queryset = self._team.members.all()
            members_field.widget.current_user = current_user

    def get_live_fields(self):
        fields = ["name", "description", "access"]
        if self.get_live_field("access") == Project.Access.INVITE_ONLY:
            fields += ["members"]
        return fields

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.team = self._team

        if commit:
            with transaction.atomic():
                instance.save()
                self.save_m2m()

        return instance
