import analytics
from rest_framework import viewsets
from rest_framework.decorators import api_view
from rest_framework.generics import get_object_or_404
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from apps.base.analytics import WORFKLOW_RUN_EVENT

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
        return Workflow.objects.filter(
            project__team__in=self.request.user.teams.all()
        ).all()


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
def workflow_out_of_date(request, pk):
    workflow = get_object_or_404(Workflow, pk=pk)
    return Response(
        {
            "isOutOfDate": workflow.out_of_date,
            "hasBeenRun": workflow.last_run is not None,
        }
    )
