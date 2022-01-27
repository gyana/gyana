from django.urls import reverse
from django.views.generic.edit import DeleteView

from apps.base.views import TurboCreateView
from apps.connectors.mixins import ConnectorMixin

from .forms import FacebookAdsCustomReportCreateForm
from .models import FacebookAdsCustomReport


class FacebookAdsCustomReportCreate(ConnectorMixin, TurboCreateView):
    template_name = "customreports/create.html"
    model = FacebookAdsCustomReport
    form_class = FacebookAdsCustomReportCreateForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["connector"] = self.connector
        return kwargs

    def get_success_url(self):
        return reverse("connectors_customreports:list", args=(self.connector.id,))


class FacebookAdsCustomReportDelete(ConnectorMixin, DeleteView):
    template_name = "customreports/delete.html"
    model = FacebookAdsCustomReport

    def get_success_url(self):
        return reverse("connectors_customreports:list", args=(self.connector.id,))
