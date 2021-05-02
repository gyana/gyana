import json

from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView
from django.views.generic.edit import DeleteView
from lib.bigquery import query_sheet
from turbo_response.views import TurboCreateView, TurboUpdateView

from .forms import DatasetForm
from .models import Dataset

# CRUDL


class DatasetList(ListView):
    template_name = "datasets/list.html"
    model = Dataset
    paginate_by = 20


class DatasetCreate(TurboCreateView):
    template_name = "datasets/create.html"
    model = Dataset
    form_class = DatasetForm
    success_url = reverse_lazy("datasets:list")


class DatasetDetail(DetailView):
    template_name = "datasets/detail.html"
    model = Dataset


class DatasetUpdate(TurboUpdateView):
    template_name = "datasets/update.html"
    model = Dataset
    form_class = DatasetForm
    success_url = reverse_lazy("datasets:list")


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

        df = query_sheet(self.object)
        context_data["table"] = df.to_html()
        return context_data


class DatasetGrid(DetailView):
    template_name = "datasets/grid.html"
    model = Dataset

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        df = query_sheet(self.object)

        context_data["columns"] = json.dumps([{"field": col} for col in df.columns])
        context_data["rows"] = df.to_json(orient="records")

        return context_data
