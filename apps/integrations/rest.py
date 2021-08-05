import datetime
import os
import time

import analytics
import coreapi
from apps.tables.models import Table
from apps.base.clients import get_bucket
from apps.base.segment_analytics import INTEGRATION_CREATED_EVENT
from celery.result import AsyncResult
from django.conf import settings
from django.http import HttpRequest
from django.http.response import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.text import slugify
from rest_framework.decorators import api_view, schema
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.schemas import AutoSchema
from turbo_response.stream import TurboStream

from .forms import CSVCreateForm, FivetranForm
from .tasks import (
    file_sync,
    poll_fivetran_historical_sync,
    send_integration_email,
    start_fivetran_integration_task,
)


@api_view(["POST"])
@schema(
    AutoSchema(
        manual_fields=[
            coreapi.Field(
                name="filename",
                required=True,
                location="form",
            ),
        ]
    )
)
def generate_signed_url(request: Request, session_key: str):
    filename = request.data["filename"]
    filename, file_extension = os.path.splitext(filename)
    path = f"{settings.CLOUD_NAMESPACE}/integrations/{filename}-{slugify(time.time())}{file_extension}"

    blob = get_bucket().blob(path)
    # This signed URL allows the client to create a Session URI to use as upload pointer.
    # Delegating this to the client, because geographic location matters when starting a session
    # https://cloud.google.com/storage/docs/access-control/signed-urls#signing-resumable
    url = blob.generate_signed_url(
        version="v4",
        expiration=datetime.timedelta(minutes=15),
        method="RESUMABLE",
    )

    request.session[session_key] = {**request.session[session_key], "file": path}

    return Response({"url": url})


@api_view(["POST"])
def start_sync(request: Request, session_key: str):
    form_data = request.session[session_key]

    file_sync_task_id = file_sync.delay(form_data["file"], form_data["project"])

    request.session[session_key] = {
        **request.session[session_key],
        "file_sync_task_id": str(file_sync_task_id),
    }

    return (
        TurboStream("integration-validate-flow")
        .replace.template(
            "integrations/file_setup/_create_flow.html",
            {
                "instance_session_key": session_key,
                "file_input_id": "id_file",
                "stage": "validate",
                "file_sync_task_id": file_sync_task_id,
                "turbo_stream_url": reverse(
                    "integrations:upload_complete",
                    args=(session_key,),
                ),
            },
        )
        .response(request)
    )


@api_view(["GET"])
def upload_complete(request: Request, session_key: str):
    form_data = request.session[session_key]
    file_sync_task_result = AsyncResult(
        request.session[session_key]["file_sync_task_id"]
    )

    if file_sync_task_result.state == "SUCCESS":
        table_id, time_elapsed = file_sync_task_result.get()
        table = get_object_or_404(Table, pk=table_id)

        integration = CSVCreateForm(data=form_data).save()
        integration.file = form_data["file"]
        integration.created_by = request.user
        integration.last_synced = datetime.datetime.now()
        integration.save()

        table.integration = integration
        table.save()

        finalise_upload_task_id = send_integration_email.delay(
            integration.id, time_elapsed
        )

        return (
            TurboStream("integration-validate-flow")
            .replace.template(
                "integrations/file_setup/_create_flow.html",
                {
                    "instance_session_key": session_key,
                    "file_input_id": "id_file",
                    "stage": "finalise",
                    "finalise_upload_task_id": finalise_upload_task_id,
                    "redirect_url": reverse(
                        "project_integrations:detail",
                        args=(integration.project.id, integration.id),
                    ),
                },
            )
            .response(request)
        )


@api_view(["GET"])
def start_fivetran_integration(request: HttpRequest, session_key: str):
    integration_data = request.session[session_key]

    task_id = start_fivetran_integration_task.delay(integration_data["fivetran_id"])

    return (
        TurboStream("integration-setup-container")
        .replace.template(
            "integrations/fivetran_setup/_flow.html",
            {
                "connector_start_task_id": task_id,
                "redirect_url": reverse(
                    "integrations:finalise-fivetran-integration",
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
