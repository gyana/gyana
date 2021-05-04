from functools import cached_property
from urllib.parse import urlparse

from apps.dataflows.serializers import NodeSerializer
from django.urls import resolve, reverse, reverse_lazy
from django.views.generic import DetailView, ListView
from django.views.generic.edit import DeleteView
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import viewsets
from rest_framework.generics import get_object_or_404
from turbo_response.views import TurboCreateView, TurboFormView, TurboUpdateView

from .forms import KIND_TO_FORM, DataflowForm
from .models import Dataflow, Node

# CRUDL


class DataflowList(ListView):
    template_name = "dataflows/list.html"
    model = Dataflow
    paginate_by = 20


class DataflowCreate(TurboCreateView):
    template_name = "dataflows/create.html"
    model = Dataflow
    form_class = DataflowForm
    success_url = reverse_lazy("dataflows:list")

    def form_valid(self, form):
        return super().form_valid(form)

    def get_success_url(self) -> str:
        # new_node = Node(dataflow=self.object, kind="input", x=0, y=0)
        # new_node.save()
        return self.success_url


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
