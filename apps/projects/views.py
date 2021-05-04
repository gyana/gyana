from django.urls import reverse_lazy
from django.views.generic import DetailView, ListView
from django.views.generic.edit import DeleteView
from turbo_response.views import TurboCreateView, TurboUpdateView

from .forms import ProjectForm
from .models import Project


class ProjectList(ListView):
    template_name = "projects/list.html"
    model = Project
    paginate_by = 20


class ProjectCreate(TurboCreateView):
    template_name = "projects/create.html"
    model = Project
    form_class = ProjectForm
    success_url = reverse_lazy('projects:list')


class ProjectDetail(DetailView):
    template_name = "projects/detail.html"
    model = Project


class ProjectUpdate(TurboUpdateView):
    template_name = "projects/update.html"
    model = Project
    form_class = ProjectForm
    success_url = reverse_lazy('projects:list')


class ProjectDelete(DeleteView):
    template_name = "projects/delete.html"
    model = Project
    success_url = reverse_lazy('projects:list')
