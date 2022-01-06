from turbo_response.views import TurboUpdateView

from apps.teams.models import Team

from .forms import TeamFlagForm


class TeamFlags(TurboUpdateView):
    model = Team
    form_class = TeamFlagForm
    template_name = "flags/team.html"
    pk_url_kwarg = "team_id"
