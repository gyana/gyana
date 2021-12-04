from django.views.generic import DetailView

from .models import Schedule


class ScheduleDetail(DetailView):
    template_name = "schedules/detail.html"
    model = Schedule
