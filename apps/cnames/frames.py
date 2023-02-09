from django.views.generic import DetailView, ListView
from django_tables2.views import SingleTableMixin

from apps.teams.mixins import TeamMixin

from .heroku import (
    HEROKU_DOMAIN_STATE_TO_ICON,
    HEROKU_DOMAIN_STATE_TO_MESSAGE,
    get_heroku_domain_status,
)
from .models import CName
from .tables import CNameTable


class CNameList(TeamMixin, SingleTableMixin, ListView):
    template_name = "cnames/list.html"
    model = CName
    table_class = CNameTable
    paginate_by = 20

    def get_queryset(self):
        return self.team.cname_set.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cname_count"] = self.team.cname_set.count()
        return context


class CNameStatus(DetailView):
    template_name = "cnames/status.html"
    model = CName

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        status = get_heroku_domain_status(self.object)
        context["status_message"] = HEROKU_DOMAIN_STATE_TO_MESSAGE[status]
        context["status_icon"] = HEROKU_DOMAIN_STATE_TO_ICON[status]
        return context
