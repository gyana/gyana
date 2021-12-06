from graphlib import CycleError

from django.urls import reverse
from django.utils import timezone
from turbo_response.views import TurboUpdateView

from apps.base.frames import TurboFrameUpdateView
from apps.projects.mixins import ProjectMixin
from apps.schedules.periodic import run_schedule

from .forms import ScheduleSettingsForm
from .models import Schedule


class ScheduleDetail(ProjectMixin, TurboUpdateView):
    template_name = "schedules/detail.html"
    model = Schedule
    fields = []

    def form_valid(self, form):
        try:
            result = run_schedule.delay(self.project.id)
            self.object.run_task_id = result.task_id
            self.object.run_started_at = timezone.now()
            self.object.save()
        except CycleError:
            # todo: add an error to the schedule to track "is_circular"
            pass
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
