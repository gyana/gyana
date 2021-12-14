from uuid import uuid4

from django.utils import timezone
import analytics
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.runs.models import JobRun

from .bigquery import run_workflow
from .models import Workflow
from .serializers import WorkflowSerializer


class WorkflowViewSet(viewsets.ModelViewSet):
    serializer_class = WorkflowSerializer
    filterset_fields = ["project"]
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        if self.request is None:
            return Workflow.objects.none()
        return Workflow.objects.filter(project__team__members=self.request.user).all()


@api_view(http_method_names=["POST"])
def workflow_run(request, pk):
    workflow = get_object_or_404(Workflow, pk=pk)
    run = JobRun.objects.create(
        source=JobRun.Source.WORKFLOW,
        workflow=workflow,
        task_id=uuid4(),
        state=JobRun.State.RUNNING,
        started_at=timezone.now(),
        user=request.user,
    )
    run_workflow.apply_async((run.id,), task_id=run.task_id)
    return Response({"task_id": run.task_id})


@api_view(http_method_names=["GET"])
def workflow_out_of_date(request, pk):
    workflow = get_object_or_404(Workflow, pk=pk)
    return Response(
        {
            "isOutOfDate": workflow.out_of_date,
            "hasBeenRun": workflow.last_success_run is not None,
            "errors": workflow.errors,
        }
    )
