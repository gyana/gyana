from django.http import Http404
from django.urls import reverse_lazy
from django_tables2.views import SingleTableMixin

from apps.base.views import UpdateView
from apps.runs.tables import GraphRunTable

from .forms import ProjectRunForm
from .models import Project
from .tasks import duplicate_project


class ProjectRuns(SingleTableMixin, UpdateView):
    template_name = "projects/runs.html"
    model = Project
    form_class = ProjectRunForm
    table_class = GraphRunTable
    paginate_by = 10
    pk_url_kwarg = "project_id"

    def get_table_data(self):
        return self.object.runs.all()

    def get_success_url(self):
        return reverse("projects:runs", args=(self.object.id,))


class ProjectDuplicate(UpdateView):
    model = Project
    fields = []
    extra_context = {"object_name": "project"}
    pk_url_kwarg = "project_id"
    template_name = "projects/duplicate.html"

    def form_valid(self, form):
        if not self.object.team.can_create_project:
            raise Http404("Cannot create new projects on the current plan")
        duplicate_project.delay(self.object.id, self.request.user.id)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["show_alert"] = True
        return context

    def get_success_url(self) -> str:
        return reverse("projects:duplicate", args=(self.object.id,))
