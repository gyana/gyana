from functools import cached_property
from urllib.parse import urlparse

from apps.dataflows.serializers import NodeSerializer
from django.urls import resolve, reverse, reverse_lazy
from django.views.generic import DetailView, ListView
from django.views.generic.edit import DeleteView
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


class DataflowMixin:
    @property
    def dataflow(self):
        resolver_match = resolve(urlparse(self.request.META["HTTP_REFERER"]).path)
        return Dataflow.objects.get(pk=resolver_match.kwargs["pk"])


class NodeViewSet(DataflowMixin, viewsets.ModelViewSet):
    serializer_class = NodeSerializer

    def get_queryset(self):
        return Node.objects.filter(dataflow=self.dataflow).all()


class NodeUpdate(TurboFormView):
    template_name = "dataflows/node.html"

    @cached_property
    def node(self):
        return get_object_or_404(Node, pk=self.kwargs["pk"])

    @cached_property
    def dataflow(self):
        return Dataflow.objects.get(pk=self.kwargs["dataflow_id"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["dataflow"] = self.dataflow
        context["node"] = self.node
        return context

    def get_form_class(self):
        return KIND_TO_FORM[self.node.kind]

    def get_initial(self):
        return self.node.config

    def form_valid(self, form):
        self.node.config = form.cleaned_data
        self.node.save()

        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse("dataflows:node", args=(self.dataflow.id, self.node.id))
