import json

from apps.projects.mixins import ProjectMixin
from django.db.models.query import QuerySet
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView, ListView
from django.views.generic.edit import DeleteView
from lib.bigquery import query_dataset, sync_table
from turbo_response.views import TurboCreateView, TurboUpdateView

from .forms import CSVForm, GoogleSheetsForm
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
    success_url = reverse_lazy("datasets:list")

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["dataset_kind"] = Dataset.Kind
        return context_data

    def get_initial(self):
        initial = super().get_initial()
        initial["kind"] = self.request.GET.get("kind")
        initial["project"] = self.project
        return initial

    def get_form_class(self):
        if (kind := self.request.GET.get("kind")) is not None:
            if kind == Dataset.Kind.GOOGLE_SHEETS:
                return GoogleSheetsForm
            elif kind == Dataset.Kind.CSV:
                return CSVForm

        return CSVForm


class DatasetDetail(DetailView):
    template_name = "datasets/detail.html"
    model = Dataset


class DatasetUpdate(TurboUpdateView):
    template_name = "datasets/update.html"
    model = Dataset
    success_url = reverse_lazy("datasets:list")

    def get_form_class(self):
        if self.object.kind == Dataset.Kind.GOOGLE_SHEETS:
            return GoogleSheetsForm
        elif self.object.kind == Dataset.Kind.CSV:
            return CSVForm


class DatasetDelete(DeleteView):
    template_name = "datasets/delete.html"
    model = Dataset
    success_url = reverse_lazy("datasets:list")


# Turbo frames


class DatasetTable(DetailView):
    template_name = "datasets/table.html"
    model = Dataset

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        df = query_dataset(self.object)
        context_data["table"] = df.to_html()
        return context_data


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
        sync_table(self.object)
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse("datasets:sync", args=(self.object.id,))
