from django_tables2 import SingleTableMixin, SingleTableView

from apps.appsumo.tables import AppsumoExtraTable
from apps.base.frames import TurboFrameListView
from apps.teams.mixins import TeamMixin

from .models import AppsumoCode, AppsumoExtra
from .tables import AppsumoCodeTable


class AppsumoCodeList(TeamMixin, SingleTableView, TurboFrameListView):
    template_name = "appsumo/list.html"
    model = AppsumoCode
    table_class = AppsumoCodeTable
    paginate_by = 20
    turbo_frame_dom_id = "team_appsumo:list"

    def get_queryset(self):
        return self.team.appsumocode_set.all()


class AppsumoExtra(TeamMixin, SingleTableMixin, TurboFrameListView):
    template_name = "appsumo/extra.html"
    model = AppsumoExtra
    table_class = AppsumoExtraTable
    turbo_frame_dom_id = "appsumo:extra"

    def get_queryset(self):
        return self.team.appsumoextra_set.all()
