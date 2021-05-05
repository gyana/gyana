from functools import cached_property

from apps.dataflows.serializers import NodeSerializer
from apps.projects.mixins import ProjectMixin
from django.db.models.query import QuerySet
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView, ListView
from django.views.generic.edit import DeleteView
from rest_framework import viewsets
from turbo_response.views import TurboCreateView, TurboUpdateView

from .forms import KIND_TO_FORM, DataflowForm
from .models import Dataflow, Node

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


class NodeUpdate(TurboUpdateView):
    template_name = "dataflows/node.html"
    model = Node

    @cached_property
    def dataflow(self):
        return Dataflow.objects.get(pk=self.kwargs["dataflow_id"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["dataflow"] = self.dataflow
        context["node"] = self.object
        return context

    def get_form_class(self):
        return KIND_TO_FORM[self.object.kind]

    def get_success_url(self) -> str:
        return reverse("dataflows:node", args=(self.dataflow.id, self.object.id))
