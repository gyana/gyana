import json

from apps.datasets.tasks import poll_fivetran_historical_sync
from apps.projects.mixins import ProjectMixin
from django.conf import settings
from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.generic import DetailView, ListView
from django.views.generic.edit import DeleteView
from lib.bigquery import create_external_table, query_dataset, sync_table
from lib.fivetran import FivetranClient, get_services
from turbo_response.views import TurboCreateView, TurboUpdateView

from .forms import CSVForm, FivetranForm, GoogleSheetsForm
from .models import Dataset

# CRUDL


class DatasetList(ProjectMixin, ListView):
    template_name = "datasets/list.html"
    model = Dataset
    paginate_by = 20

    def get_queryset(self) -> QuerySet:
        return Dataset.objects.filter(project=self.project).all()


class DatasetCreate(ProjectMixin, TurboCreateView):
    template_name = "datasets/create.html"
    model = Dataset

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["dataset_kind"] = Dataset.Kind

        if (
            self.request.GET.get("kind") == Dataset.Kind.FIVETRAN
            and self.request.GET.get("service") is None
        ):
            context_data["services"] = get_services()
        return context_data

    def get_initial(self):
        initial = super().get_initial()
        initial["kind"] = self.request.GET.get("kind")
        initial["service"] = self.request.GET.get("service")
        initial["project"] = self.project
        return initial

    def get_form_class(self):
        if (kind := self.request.GET.get("kind")) is not None:
            if kind == Dataset.Kind.GOOGLE_SHEETS:
                return GoogleSheetsForm
            elif kind == Dataset.Kind.CSV:
                return CSVForm
            elif kind == Dataset.Kind.FIVETRAN:
                return FivetranForm

        return CSVForm

    def get_success_url(self) -> str:
        return reverse("projects:datasets:list", args=(self.project.id,))


class DatasetDetail(ProjectMixin, DetailView):
    template_name = "datasets/detail.html"
    model = Dataset


class DatasetUpdate(ProjectMixin, TurboUpdateView):
    template_name = "datasets/update.html"
    model = Dataset

    def get_form_class(self):
        if self.object.kind == Dataset.Kind.GOOGLE_SHEETS:
            return GoogleSheetsForm
        elif self.object.kind == Dataset.Kind.CSV:
            return CSVForm

    def get_success_url(self) -> str:
        return reverse("projects:datasets:list", args=(self.project.id,))


class DatasetDelete(ProjectMixin, DeleteView):
    template_name = "datasets/delete.html"
    model = Dataset

    def get_success_url(self) -> str:
        return reverse("projects:datasets:list", args=(self.project.id,))


# Turbo frames


class DatasetGrid(DetailView):
    template_name = "datasets/grid.html"
    model = Dataset

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        df = query_dataset(self.object)

        context_data["columns"] = json.dumps([{"field": col} for col in df.columns])
        context_data["rows"] = df.to_json(orient="records")

        return context_data


class DatasetSync(TurboUpdateView):
    template_name = "datasets/sync.html"
    model = Dataset
    fields = []

    def form_valid(self, form):
        external_table_id = create_external_table(self.object)
        sync_table(self.object, external_table_id)
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse("datasets:sync", args=(self.object.id,))


# Turbo frames


class DatasetAuthorize(DetailView):

    model = Dataset
    template_name = "datasets/authorize.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        dataset = context["dataset"]

        if dataset.fivetran_id is None:
            FivetranClient(dataset).create()

        return context


# Endpoints


def authorize_fivetran(request: HttpRequest, pk: int):

    dataset = get_object_or_404(Dataset, pk=pk)
    uri = reverse("datasets:authorize-fivetran-redirect", args=(pk,))
    redirect_uri = (
        f"{settings.EXTERNAL_URL}{uri}?original_uri={request.GET.get('original_uri')}"
    )

    return FivetranClient(dataset).authorize(redirect_uri)


def authorize_fivetran_redirect(request: HttpRequest, pk: int):

    dataset = get_object_or_404(Dataset, pk=pk)
    dataset.fivetran_authorized = True

    result = poll_fivetran_historical_sync.delay(dataset.id)
    dataset.fivetran_poll_historical_sync_task_id = result.task_id

    dataset.save()

    return redirect(request.GET.get("original_uri"))
