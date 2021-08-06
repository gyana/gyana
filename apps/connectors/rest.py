import analytics
from apps.base.segment_analytics import INTEGRATION_CREATED_EVENT
from django.http import HttpRequest
from django.http.response import HttpResponseRedirect
from django.urls import reverse
from rest_framework.decorators import api_view
from turbo_response.stream import TurboStream

from .forms import FivetranForm
from .tasks import poll_fivetran_historical_sync, start_fivetran_integration_task


@api_view(["GET"])
def start_fivetran_integration(request: HttpRequest, session_key: str):
    integration_data = request.session[session_key]

    task_id = start_fivetran_integration_task.delay(integration_data["fivetran_id"])

    return (
        TurboStream("integration-setup-container")
        .replace.template(
            "connectors/fivetran_setup/_flow.html",
            {
                "connector_start_task_id": task_id,
                "redirect_url": reverse(
                    "connectors:finalise-fivetran-integration",
                    args=(session_key,),
                ),
            },
        )
        .response(request)
    )


@api_view(["GET"])
def finalise_fivetran_integration(request: HttpRequest, session_key: str):
    integration_data = request.session[session_key]
    # Create integration
    integration = FivetranForm(data=integration_data).save()
    integration.schema = integration_data["schema"]
    integration.fivetran_id = integration_data["fivetran_id"]
    integration.created_by = request.user
    # Start polling
    task_id = poll_fivetran_historical_sync.delay(integration.id)
    integration.fivetran_poll_historical_sync_task_id = str(task_id)
    integration.save()

    analytics.track(
        request.user.id,
        INTEGRATION_CREATED_EVENT,
        {
            "id": integration.id,
            "type": integration.kind,
            "name": integration.name,
        },
    )

    return HttpResponseRedirect(
        reverse(
            "project_integrations:detail",
            args=(integration.project.id, integration.id),
        )
    )
