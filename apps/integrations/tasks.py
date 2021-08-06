import analytics
from apps.base.segment_analytics import INTEGRATION_SYNC_SUCCESS_EVENT
from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMessage
from django.shortcuts import get_object_or_404
from django.urls import reverse

from .models import Integration


@shared_task(bind=True)
def send_integration_email(self, integration_id: int, time_elapsed: int):
    integration = get_object_or_404(Integration, pk=integration_id)

    url = reverse(
        "project_integrations:detail",
        args=(
            integration.project.id,
            integration_id,
        ),
    )

    creator = integration.created_by

    if integration.enable_sync_emails:
        message = EmailMessage(
            subject=None,
            from_email="Gyana Notifications <notifications@gyana.com>",
            to=[creator.email],
        )
        # This id points to the sync success template in SendGrid
        message.template_id = "d-5f87a7f6603b44e09b21cfdcf6514ffa"
        message.merge_data = {
            creator.email: {
                "userName": creator.first_name or creator.email.split("@")[0],
                "integrationName": integration.name,
                "integrationHref": settings.EXTERNAL_URL + url,
                "projectName": integration.project.name,
            }
        }
        message.esp_extra = {
            "asm": {
                # The "App Notifications" Unsubscribe group
                "group_id": 17220,
            },
        }
        message.send()

    analytics.track(
        creator.id,
        INTEGRATION_SYNC_SUCCESS_EVENT,
        {
            "id": integration.id,
            "kind": integration.kind,
            "row_count": integration.num_rows,
            "time_to_sync": time_elapsed,
        },
    )

    return integration_id
