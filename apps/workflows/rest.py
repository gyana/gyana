import analytics
from apps.base.segment_analytics import WORFKLOW_RUN_EVENT
from rest_framework.decorators import api_view
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from .bigquery import run_workflow
from .models import Workflow


@api_view(http_method_names=["POST"])
def workflow_run(request, pk):
    workflow = get_object_or_404(Workflow, pk=pk)
    errors = run_workflow(workflow) or {}

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
def worflow_out_of_date(request, pk):
    workflow = get_object_or_404(Workflow, pk=pk)
    return Response(
        {
            "isOutOfDate": workflow.out_of_date,
            "hasBeenRun": workflow.last_run is not None,
        }
    )
