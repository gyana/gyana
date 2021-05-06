import json
from functools import cached_property

from apps.dataflows.serializers import NodeSerializer
from apps.projects.mixins import ProjectMixin
from django import forms
from django.db.models.query import QuerySet
from django.http.response import HttpResponse
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView, ListView
from django.views.generic.edit import DeleteView
from lib.bigquery import ibis_client
from rest_framework import viewsets
from turbo_response.views import TurboCreateView, TurboUpdateView

from .forms import KIND_TO_FORM, DataflowForm
from .models import Column, Dataflow, Node

# CRUDL


class DataflowList(ProjectMixin, ListView):
    template_name = "dataflows/list.html"
    model = Dataflow
    paginate_by = 20

    def get_queryset(self) -> QuerySet:
        return Dataflow.objects.filter(project=self.project).all()


class DataflowCreate(ProjectMixin, TurboCreateView):
    template_name = "dataflows/create.html"
    model = Dataflow
    form_class = DataflowForm
    success_url = reverse_lazy("dataflows:list")

    def get_initial(self):
        initial = super().get_initial()
        initial["project"] = self.project
        return initial


class DataflowDetail(DetailView):
    template_name = "dataflows/detail.html"
    model = Dataflow

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["nodes"] = [{"label": e.label, "value": e.value} for e in Node.Kind]
        return context


class DataflowUpdate(TurboUpdateView):
    template_name = "dataflows/update.html"
    model = Dataflow
    form_class = DataflowForm
    success_url = reverse_lazy("dataflows:list")


class DataflowDelete(DeleteView):
    template_name = "dataflows/delete.html"
    model = Dataflow
    success_url = reverse_lazy("dataflows:list")


# Nodes


class NodeViewSet(viewsets.ModelViewSet):
    serializer_class = NodeSerializer
    queryset = Node.objects.all()
    filterset_fields = ["dataflow"]


class DefaultNodeUpdate(TurboUpdateView):
    template_name = "dataflows/sidebar/base.html"
    model = Node

    @cached_property
    def dataflow(self):
        return Dataflow.objects.get(pk=self.kwargs["dataflow_id"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["dataflow"] = self.dataflow
        context["node"] = self.object
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        if self.object.kind == "select":
            query = self.object.parents.first().get_query()
            kwargs["columns"] = (
                [(name, name) for name in query.schema()] if query is not None else []
            )

        return kwargs

    # TODO: Move this form_valid to a separate NodeUpdate inherited class
    def form_valid(self, form: forms.Form) -> HttpResponse:
        if self.object.kind == "select":
            self.object.select_columns.all().delete()
            self.object.select_columns.set(
                [Column(name=name) for name in form.cleaned_data["select_columns"]],
                bulk=False,
            )

        return super().form_valid(form)

    def get_form_class(self):
        return KIND_TO_FORM[self.object.kind]

    def get_success_url(self) -> str:
        return reverse("dataflows:node", args=(self.dataflow.id, self.object.id))


def node_update(request, *args, **kwargs):
    return DefaultNodeUpdate.as_view()(request, *args, **kwargs)


class NodeGrid(DetailView):
    template_name = "dataflows/grid.html"
    model = Node

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        conn = ibis_client()

        if (query := self.object.get_query()) is None:
            context["columns"] = []
            context["rows"] = []
            return context

        df = conn.execute(query.limit(100))
        context["columns"] = json.dumps([{"field": col} for col in df.columns])
        context["rows"] = df.to_json(orient="records")
        return context
