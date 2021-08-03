from django.views.generic import DetailView

from .models import Workflow


class WorkflowLastRun(DetailView):
    template_name = "workflows/last_run.html"
    model = Workflow
