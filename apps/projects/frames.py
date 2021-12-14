from django.urls import reverse
from django_tables2.views import SingleTableMixin

from apps.base.frames import TurboFrameUpdateView
from apps.runs.tables import GraphRunTable

from .forms import ProjectUpdateForm
from .models import Project


class ProjectRuns(SingleTableMixin, TurboFrameUpdateView):
    template_name = "projects/runs.html"
    model = Project
    form_class = ProjectUpdateForm
    table_class = GraphRunTable
    paginate_by = 10
    turbo_frame_dom_id = "projects:runs"

    def get_table_data(self):
        return self.object.runs.all()

    def get_success_url(self):
        return reverse("projects:runs", args=(self.project.id,))
