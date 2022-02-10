import analytics
from django.conf import settings
from django.core.mail.message import EmailMultiAlternatives
from django.template.loader import render_to_string
from django.urls import reverse

from apps.base.analytics import INTEGRATION_SYNC_SUCCESS_EVENT
from apps.integrations.models import Integration
from apps.users.models import CustomUser

from .models import Integration


def send_integration_ready_email(integration, time_to_sync=None):

    if integration.created_by:
        email = integration_ready_email(integration, integration.created_by)
        email.send()

        analytics.track(
            integration.created_by.id,
            INTEGRATION_SYNC_SUCCESS_EVENT,
            {
                "id": integration.id,
                "kind": integration.kind,
                "row_count": integration.num_rows,
                "time_to_sync": time_to_sync,
            },
        )


def integration_ready_email(integration: Integration, recipient: CustomUser):
    url = reverse(
        "project_integrations:detail",
        args=(
            integration.project.id,
            integration.id,
        ),
    )

    context = {
        "integration_name": integration.name,
        "integration_link": settings.EXTERNAL_URL + url,
        "project_name": integration.project.name,
    }
    subject = render_to_string(
        "integrations/email/integration_ready_subject.txt", context
    ).strip()
    text_body = render_to_string(
        "integrations/email/integration_ready_message.txt", context
    )
    html_body = render_to_string(
        "integrations/email/integration_ready_message.html", context
    )

    message = EmailMultiAlternatives(
        subject=subject,
        from_email="Gyana Notifications <notifications@gyana.com>",
        to=[recipient.email],
        body=text_body,
    )
    message.attach_alternative(html_body, "text/html")

    return message
