from django.urls import reverse
from django_tables2.views import SingleTableMixin

from apps.base.frames import TurboFrameUpdateView
from apps.runs.tables import GraphRunTable

from .forms import ProjectRunForm
from .models import Project
from .tasks import duplicate_project


class ProjectRuns(SingleTableMixin, TurboFrameUpdateView):
    template_name = "projects/runs.html"
    model = Project
    form_class = ProjectRunForm
    table_class = GraphRunTable
    paginate_by = 10
    turbo_frame_dom_id = "projects:runs"
    pk_url_kwarg = "project_id"

    def get_table_data(self):
        return self.object.runs.all()

    def get_success_url(self):
        return reverse("projects:runs", args=(self.object.id,))


class ProjectDuplicate(TurboFrameUpdateView):
    model = Project
    fields = []
    extra_context = {"object_name": "project"}
    pk_url_kwarg = "project_id"
    template_name = "projects/duplicate.html"
    turbo_frame_dom_id = "projects:duplicate"

    def form_valid(self, form):
        duplicate_project.delay(self.object.id, self.request.user.id)
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["show_alert"] = True
        return context

    def get_success_url(self) -> str:
        return reverse("projects:duplicate", args=(self.object.id,))
