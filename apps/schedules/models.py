from datetime import time

from django.db import models
from django_celery_beat.models import PeriodicTask

from apps.base.models import BaseModel
from apps.projects.models import Project


class Schedule(BaseModel):
    # default midnight
    daily_schedule_time = models.TimeField(default=time())
    periodic_task = models.OneToOneField(
        PeriodicTask, null=True, on_delete=models.SET_NULL
    )
    project = models.OneToOneField(Project, on_delete=models.CASCADE)
