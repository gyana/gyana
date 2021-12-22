from django.urls import reverse
from django_tables2.views import SingleTableMixin

from apps.base.frames import TurboFrameUpdateView
from apps.runs.tables import GraphRunTable

from .forms import ProjectRunForm
from .models import Project


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
