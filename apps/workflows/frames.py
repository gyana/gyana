from apps.utils.frames import TurboFrameDetailView

from .models import Workflow


class WorkflowLastRun(TurboFrameDetailView):
    template_name = "workflows/last_run.html"
    model = Workflow
    turbo_frame_dom_id = "workflow-last-run"
