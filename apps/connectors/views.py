from apps.connectors.tasks import poll_fivetran_historical_sync
from apps.projects.mixins import ProjectMixin
from django.conf import settings
from django.db.models.query import QuerySet
from django.http.request import HttpRequest
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView, ListView
from django.views.generic.edit import DeleteView
from lib.fivetran import FivetranClient, get_services
from turbo_response.views import TurboCreateView, TurboUpdateView

from .forms import ConnectorForm
from .models import Connector


class ConnectorList(ProjectMixin, ListView):
    template_name = "connectors/list.html"
    model = Connector
    paginate_by = 20

    def get_queryset(self) -> QuerySet:
        return Connector.objects.filter(project=self.project).all()


class ConnectorCreate(ProjectMixin, TurboCreateView):
    template_name = "connectors/create.html"
    model = Connector
    form_class = ConnectorForm
    success_url = reverse_lazy("connectors:list")

    def get_context_data(self, **kwargs):

        context = super().get_context_data(**kwargs)

        if (service := self.request.GET.get("service")) is None:
            context["services"] = get_services()

        return context

    def get_initial(self):
        initial = super().get_initial()
        initial["project"] = self.project

        if (service := self.request.GET.get("service")) is not None:
            initial["service"] = service

        return initial


class ConnectorDetail(DetailView):
    template_name = "connectors/detail.html"
    model = Connector


class ConnectorUpdate(TurboUpdateView):
    template_name = "connectors/update.html"
    model = Connector
    form_class = ConnectorForm
    success_url = reverse_lazy("connectors:list")


class ConnectorDelete(DeleteView):
    template_name = "connectors/delete.html"
    model = Connector
    success_url = reverse_lazy("connectors:list")


# Turbo frames


class ConnectorAuthorize(DetailView):

    model = Connector
    template_name = "connectors/authorize.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        connector = context["connector"]

        if connector.fivetran_id is None:
            FivetranClient(connector).create()

        return context


# Endpoints


def authorize_fivetran(request: HttpRequest, pk: int):

    connector = get_object_or_404(Connector, pk=pk)
    uri = reverse("connectors:authorize-fivetran-redirect", args=(pk,))
    redirect_uri = (
        f"{settings.EXTERNAL_URL}{uri}?original_uri={request.GET.get('original_uri')}"
    )

    return FivetranClient(connector).authorize(redirect_uri)


def authorize_fivetran_redirect(request: HttpRequest, pk: int):

    connector = get_object_or_404(Connector, pk=pk)
    connector.fivetran_authorized = True

    result = poll_fivetran_historical_sync.delay(connector.id)
    connector.fivetran_poll_historical_sync_task_id = result.task_id

    connector.save()

    return redirect(request.GET.get("original_uri"))
