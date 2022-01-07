from django.urls import reverse

from apps.base.turbo import TurboUpdateView
from apps.teams.models import Team

from .forms import TeamFlagForm


class TeamFlags(TurboUpdateView):
    model = Team
    form_class = TeamFlagForm
    template_name = "flags/team.html"
    pk_url_kwarg = "team_id"

    def get_success_url(self) -> str:
        return reverse("team_flags:team", args=(self.object.id,))
