from django.urls import reverse
from turbo_response.views import TurboUpdateView

from apps.projects.mixins import ProjectMixin

from .models import Schedule
from .periodic import run_all_workflows


class ScheduleDetail(ProjectMixin, TurboUpdateView):
    template_name = "schedules/detail.html"
    model = Schedule
    fields = []

    def form_valid(self, form):
        run_all_workflows(self.project, override=True)
        return super().form_valid(form)

    def get_object(self):
        return self.project.schedule

    def get_success_url(self):
        return reverse("project_schedule:detail", args=(self.project.id,))
