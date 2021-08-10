from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView
from django.views.generic.edit import DeleteView
from django_tables2 import SingleTableView
from apps.base.turbo import TurboCreateView, TurboUpdateView

from .forms import {{ cookiecutter.model_name }}Form
from .models import {{ cookiecutter.model_name }}
from .tables import {{ cookiecutter.model_name }}Table


class {{ cookiecutter.model_name }}List(SingleTableView):
    template_name = "{{ cookiecutter.app_name }}/list.html"
    model = {{ cookiecutter.model_name }}
    table_class = {{ cookiecutter.model_name }}Table
    paginate_by = 20


class {{ cookiecutter.model_name }}Create(TurboCreateView):
    template_name = "{{ cookiecutter.app_name }}/create.html"
    model = {{ cookiecutter.model_name }}
    form_class = {{ cookiecutter.model_name }}Form
    success_url = reverse_lazy('{{ cookiecutter.app_name }}:list')


class {{ cookiecutter.model_name }}Detail(DetailView):
    template_name = "{{ cookiecutter.app_name }}/detail.html"
    model = {{ cookiecutter.model_name }}


class {{ cookiecutter.model_name }}Update(TurboUpdateView):
    template_name = "{{ cookiecutter.app_name }}/update.html"
    model = {{ cookiecutter.model_name }}
    form_class = {{ cookiecutter.model_name }}Form
    success_url = reverse_lazy('{{ cookiecutter.app_name }}:list')


class {{ cookiecutter.model_name }}Delete(DeleteView):
    template_name = "{{ cookiecutter.app_name }}/delete.html"
    model = {{ cookiecutter.model_name }}
    success_url = reverse_lazy('{{ cookiecutter.app_name }}:list')
