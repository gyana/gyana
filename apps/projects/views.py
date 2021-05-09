from django import forms
from django.db.models.query import QuerySet
from django.http import HttpResponse
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

    def get_queryset(self) -> QuerySet:
        return Project.objects.filter(team=self.request.user.teams.first()).all()


class ProjectCreate(TurboCreateView):
    template_name = "projects/create.html"
    model = Project
    form_class = ProjectForm
    success_url = reverse_lazy("projects:list")

    def get_initial(self):
        initial = super().get_initial()
        initial["team"] = self.request.user.teams.first()
        return initial


class ProjectDetail(DetailView):
    template_name = "projects/detail.html"
    model = Project


class ProjectUpdate(TurboUpdateView):
    template_name = "projects/update.html"
    model = Project
    form_class = ProjectForm
    success_url = reverse_lazy("projects:list")


class ProjectDelete(DeleteView):
    template_name = "projects/delete.html"
    model = Project
    success_url = reverse_lazy("projects:list")


class ProjectConnectors(DetailView):
    template_name = "projects/connectors.html"
    model = Project


class ProjectDatasets(DetailView):
    template_name = "projects/datasets.html"
    model = Project


class ProjectDataflows(DetailView):
    template_name = "projects/dataflows.html"
    model = Project


class ProjectDashboards(DetailView):
    template_name = "projects/dashboards.html"
    model = Project
