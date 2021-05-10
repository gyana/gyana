from apps.dashboards.tables import DashboardTable
from apps.projects.mixins import ProjectMixin
from django.db.models.query import QuerySet
from django.urls import reverse_lazy
from django.urls.base import reverse
from django.views.generic import DetailView
from django.views.generic.edit import DeleteView
from django_tables2 import SingleTableView
from turbo_response.views import TurboCreateView, TurboUpdateView

from .forms import DashboardForm
from .models import Dashboard


class DashboardList(ProjectMixin, SingleTableView):
    template_name = "dashboards/list.html"
    model = Dashboard
    table_class = DashboardTable
    paginate_by = 20

    def get_queryset(self) -> QuerySet:
        return Dashboard.objects.filter(project=self.project).all()


class DashboardCreate(ProjectMixin, TurboCreateView):
    template_name = "dashboards/create.html"
    model = Dashboard
    form_class = DashboardForm
    success_url = reverse_lazy("projects:dashboards:list")

    def get_initial(self):
        initial = super().get_initial()
        initial["project"] = self.project
        return initial

    def get_success_url(self) -> str:
        return reverse(
            "projects:dashboards:detail", args=(self.project.id, self.object.id)
        )


class DashboardDetail(ProjectMixin, DetailView):
    template_name = "dashboards/detail.html"
    model = Dashboard


class DashboardUpdate(ProjectMixin, TurboUpdateView):
    template_name = "dashboards/update.html"
    model = Dashboard
    form_class = DashboardForm

    def get_success_url(self) -> str:
        return reverse(
            "projects:dashboards:detail", args=(self.project.id, self.object.id)
        )


class DashboardDelete(ProjectMixin, DeleteView):
    template_name = "dashboards/delete.html"
    model = Dashboard

    def get_success_url(self) -> str:
        return reverse("projects:dashboards:list", args=(self.project.id,))
