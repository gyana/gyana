from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView
from django.views.generic.edit import DeleteView
from turbo_response.views import TurboCreateView, TurboUpdateView

from .forms import ConnectorForm
from .models import Connector


class ConnectorList(ListView):
    template_name = "connectors/list.html"
    model = Connector
    paginate_by = 20


class ConnectorCreate(TurboCreateView):
    template_name = "connectors/create.html"
    model = Connector
    form_class = ConnectorForm
    success_url = reverse_lazy('connectors:list')


class ConnectorDetail(DetailView):
    template_name = "connectors/detail.html"
    model = Connector


class ConnectorUpdate(TurboUpdateView):
    template_name = "connectors/update.html"
    model = Connector
    form_class = ConnectorForm
    success_url = reverse_lazy('connectors:list')


class ConnectorDelete(DeleteView):
    template_name = "connectors/delete.html"
    model = Connector
    success_url = reverse_lazy('connectors:list')
