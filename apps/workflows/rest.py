import analytics
from django.utils import timezone
from rest_framework.decorators import api_view
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from apps.base.analytics import WORFKLOW_RUN_EVENT
from apps.runs.models import JobRun

from .bigquery import run_workflow
from .models import Workflow


@api_view(http_method_names=["POST"])
def workflow_run(request, pk):
    workflow = get_object_or_404(Workflow, pk=pk)
    run = JobRun.objects.create(
        source=JobRun.Source.WORKFLOW,
        workflow=workflow,
        state=JobRun.State.RUNNING,
        started_at=timezone.now(),
    )
    errors = run_workflow(workflow, run) or {}

    analytics.track(
        request.user.id,
        WORFKLOW_RUN_EVENT,
        {
            "id": workflow.id,
            "success": not bool(errors),
            **{f"error_{idx}": errors[key] for idx, key in enumerate(errors.keys())},
        },
    )

    return Response(errors)


@api_view(http_method_names=["GET"])
def workflow_out_of_date(request, pk):
    workflow = get_object_or_404(Workflow, pk=pk)
    return Response(
        {
            "isOutOfDate": workflow.out_of_date,
            "hasBeenRun": workflow.last_run is not None,
        }
    )
