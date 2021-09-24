from django_tables2.views import SingleTableMixin

from apps.base.frames import TurboFrameListView
from apps.teams.mixins import TeamMixin

from .models import CName
from .tables import CNameTable


class CNameList(TeamMixin, SingleTableMixin, TurboFrameListView):
    template_name = "cnames/list.html"
    model = CName
    table_class = CNameTable
    paginate_by = 20
    turbo_frame_dom_id = "cnames:list"

    def get_queryset(self):
        return self.team.cname_set.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cname_count"] = self.team.cname_set.count()
        return context
