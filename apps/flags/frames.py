from apps.base.frames import TurboFrameUpdateView
from apps.teams.models import Team

from .forms import TeamFlagForm


class TeamFlags(TurboFrameUpdateView):
    model = Team
    form_class = TeamFlagForm
    template_name = "flags/team.html"
    pk_url_kwarg = "team_id"
    turbo_frame_dom_id = 'team_flags:team'
