from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView
from django.views.generic.edit import DeleteView
from django_tables2 import SingleTableView
from turbo_response.views import TurboCreateView, TurboUpdateView

from .forms import NodeForm
from .models import Node
from .tables import NodeTable


class NodeList(SingleTableView):
    template_name = "nodes/list.html"
    model = Node
    table_class = NodeTable
    paginate_by = 20


class NodeCreate(TurboCreateView):
    template_name = "nodes/create.html"
    model = Node
    form_class = NodeForm
    success_url = reverse_lazy('nodes:list')


class NodeDetail(DetailView):
    template_name = "nodes/detail.html"
    model = Node


class NodeUpdate(TurboUpdateView):
    template_name = "nodes/update.html"
    model = Node
    form_class = NodeForm
    success_url = reverse_lazy('nodes:list')


class NodeDelete(DeleteView):
    template_name = "nodes/delete.html"
    model = Node
    success_url = reverse_lazy('nodes:list')
