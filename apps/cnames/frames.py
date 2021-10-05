from django_tables2.views import SingleTableMixin

from apps.base.frames import TurboFrameDetailView, TurboFrameListView
from apps.teams.mixins import TeamMixin

from .heroku import (
    HEROKU_DOMAIN_STATE_TO_ICON,
    HEROKU_DOMAIN_STATE_TO_MESSAGE,
    get_heroku_domain_status,
)
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


class CNameStatus(TurboFrameDetailView):
    template_name = "cnames/status.html"
    model = CName
    turbo_frame_dom_id = "cnames:status"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        status = get_heroku_domain_status(self.object)
        context["status_message"] = HEROKU_DOMAIN_STATE_TO_MESSAGE[status]
        context["status_icon"] = HEROKU_DOMAIN_STATE_TO_ICON[status]
        return context
