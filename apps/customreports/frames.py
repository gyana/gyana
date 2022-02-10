from django.urls import reverse
from django_tables2 import SingleTableMixin

from apps.base.frames import TurboFrameListView, TurboFrameUpdateView
from apps.connectors.mixins import ConnectorMixin

from .forms import FacebookAdsCustomReportUpdateForm
from .models import FacebookAdsCustomReport
from .tables import FacebookAdsCustomReportTable


class FacebookAdsCustomReportList(ConnectorMixin, SingleTableMixin, TurboFrameListView):
    template_name = "customreports/list.html"
    model = FacebookAdsCustomReport
    table_class = FacebookAdsCustomReportTable
    paginate_by = 20
    turbo_frame_dom_id = "customreports:list"

    def get_queryset(self):
        return self.connector.facebookadscustomreport_set.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context[
            "facebookadscustomreport_count"
        ] = self.connector.facebookadscustomreport_set.count()
        return context


class FacebookAdsCustomReportUpdate(ConnectorMixin, TurboFrameUpdateView):
    template_name = "customreports/update.html"
    model = FacebookAdsCustomReport
    form_class = FacebookAdsCustomReportUpdateForm
    turbo_frame_dom_id = "customreports:update"

    def get_success_url(self) -> str:
        return reverse(
            "connectors_customreports:update", args=(self.connector.id, self.object.id)
        )
