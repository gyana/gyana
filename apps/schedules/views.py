from django.views.generic import DetailView

from apps.projects.mixins import ProjectMixin

from .models import Schedule


class ScheduleDetail(ProjectMixin, DetailView):
    def get_object(self):
        return self.project.schedule

    template_name = "schedules/detail.html"
    model = Schedule
