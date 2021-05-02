from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView
from django.views.generic.edit import DeleteView
from turbo_response.views import TurboCreateView, TurboUpdateView

from .forms import WidgetForm
from .models import Widget


class WidgetList(ListView):
    template_name = "widgets/list.html"
    model = Widget
    paginate_by = 20


class WidgetCreate(TurboCreateView):
    template_name = "widgets/create.html"
    model = Widget
    form_class = WidgetForm
    success_url = reverse_lazy('widgets:list')


class WidgetDetail(DetailView):
    template_name = "widgets/detail.html"
    model = Widget


class WidgetUpdate(TurboUpdateView):
    template_name = "widgets/update.html"
    model = Widget
    form_class = WidgetForm
    success_url = reverse_lazy('widgets:list')


class WidgetDelete(DeleteView):
    template_name = "widgets/delete.html"
    model = Widget
    success_url = reverse_lazy('widgets:list')
