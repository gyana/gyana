import analytics
from apps.base.analytics import PROJECT_CREATED_EVENT
from apps.base.turbo import TurboCreateView, TurboUpdateView
from apps.teams.mixins import TeamMixin
from django.shortcuts import redirect
from django.urls.base import reverse
from django.views.generic import DetailView
from django.views.generic.edit import DeleteView

from .forms import ProjectForm
from .models import Project
from .tables import ProjectDashboardTable, ProjectIntegrationTable, ProjectWorkflowTable


class ProjectCreate(TeamMixin, TurboCreateView):
    template_name = "projects/create.html"
    model = Project
    form_class = ProjectForm

    def get_initial(self):
        initial = super().get_initial()
        initial["team"] = self.team
        return initial

    def get_success_url(self) -> str:
        return reverse("projects:detail", args=(self.object.id,))

    def form_valid(self, form):
        redirect = super().form_valid(form)
        analytics.track(
            self.request.user.id, PROJECT_CREATED_EVENT, {"id": form.instance.id}
        )
        return redirect


class ProjectDetail(DetailView):
    template_name = "projects/detail.html"
    model = Project
    pk_url_kwarg = "project_id"

    def get(self, request, *args, **kwargs):
        object = self.get_object()
        if not object.is_ready:
            return redirect("project_templateinstances:list", object.id)
        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        object = self.get_object()

        context_data["integrations"] = ProjectIntegrationTable(
            object.integration_set.filter(ready=True).all()[:3]
        )
        context_data["workflows"] = ProjectWorkflowTable(object.workflow_set.all()[:3])
        context_data["dashboards"] = ProjectDashboardTable(
            object.dashboard_set.all()[:3]
        )

        return context_data


class ProjectUpdate(TurboUpdateView):
    template_name = "projects/update.html"
    model = Project
    form_class = ProjectForm
    pk_url_kwarg = "project_id"

    def get_success_url(self) -> str:
        return reverse("projects:detail", args=(self.object.id,))


class ProjectDelete(DeleteView):
    template_name = "projects/delete.html"
    model = Project
    pk_url_kwarg = "project_id"

    def get_success_url(self) -> str:
        return reverse("teams:detail", args=(self.object.team.id,))


class ProjectSettings(DetailView):
    template_name = "projects/settings.html"
    model = Project
    pk_url_kwarg = "project_id"
