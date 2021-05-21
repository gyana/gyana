from django.db.models.query import QuerySet
from django.urls import reverse_lazy
from django.urls.base import reverse
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

    def get_initial(self):
        initial = super().get_initial()
        initial["team"] = self.request.user.teams.first()
        return initial

    def get_success_url(self) -> str:
        return reverse("projects:detail", args=(self.object.id,))


class ProjectDetail(DetailView):
    template_name = "projects/detail.html"
    model = Project

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        object = self.get_object()

        context_data["integration_count"] = object.integration_set.count()
        context_data["workflow_count"] = object.workflow_set.count()
        context_data["dashboard_count"] = object.dashboard_set.count()

        context_data["integration_pending"] = object.integration_set.filter(
            last_synced=None
        ).count()
        context_data["workflow_error"] = object.workflow_set.filter(
            nodes__error__isnull=False
        ).count()
        return context_data


class ProjectUpdate(TurboUpdateView):
    template_name = "projects/update.html"
    model = Project
    form_class = ProjectForm

    def get_success_url(self) -> str:
        return reverse("projects:settings", args=(self.object.id,))


class ProjectDelete(DeleteView):
    template_name = "projects/delete.html"
    model = Project
    success_url = reverse_lazy("projects:list")


class ProjectSettings(DetailView):
    template_name = "projects/settings.html"
    model = Project
