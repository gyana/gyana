from apps.appsumo.tables import AppsumoExtraTable
from apps.base.frames import TurboFrameListView
from apps.teams.mixins import TeamMixin
from django_tables2 import SingleTableMixin

from .models import AppsumoExtra


class AppsumoExtra(TeamMixin, SingleTableMixin, TurboFrameListView):
    template_name = "appsumo/extra.html"
    model = AppsumoExtra
    table_class = AppsumoExtraTable
    turbo_frame_dom_id = "appsumo:extra"

    def get_queryset(self):
        return self.team.appsumoextra_set.all()
