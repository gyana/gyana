from django.urls import reverse
from turbo_response.views import TurboUpdateView

from apps.base.frames import TurboFrameUpdateView
from apps.projects.mixins import ProjectMixin

from .forms import ScheduleSettingsForm
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


class ScheduleSettings(ProjectMixin, TurboFrameUpdateView):
    template_name = "schedules/settings.html"
    model = Schedule
    form_class = ScheduleSettingsForm
    turbo_frame_dom_id = "project_schedule:settings"

    def get_object(self):
        return self.project.schedule

    def get_success_url(self):
        return reverse("project_schedule:settings", args=(self.project.id,))
