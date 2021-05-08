from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView
from django.views.generic.edit import DeleteView
from turbo_response.views import TurboCreateView, TurboUpdateView

from .forms import TableForm
from .models import Table


class TableList(ListView):
    template_name = "tables/list.html"
    model = Table
    paginate_by = 20


class TableCreate(TurboCreateView):
    template_name = "tables/create.html"
    model = Table
    form_class = TableForm
    success_url = reverse_lazy('tables:list')


class TableDetail(DetailView):
    template_name = "tables/detail.html"
    model = Table


class TableUpdate(TurboUpdateView):
    template_name = "tables/update.html"
    model = Table
    form_class = TableForm
    success_url = reverse_lazy('tables:list')


class TableDelete(DeleteView):
    template_name = "tables/delete.html"
    model = Table
    success_url = reverse_lazy('tables:list')
