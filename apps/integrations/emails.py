from apps.integrations.models import Integration
from apps.users.models import CustomUser
from django.conf import settings
from django.core.mail import EmailMessage
from django.urls import reverse

from .models import Integration


def integration_ready_email(integration: Integration, recipient: CustomUser):

    url = reverse(
        "project_integrations:detail",
        args=(
            integration.project.id,
            integration.id,
        ),
    )

    message = EmailMessage(
        subject=None,
        from_email="Gyana Notifications <notifications@gyana.com>",
        to=[recipient.email],
    )
    # This id points to the sync success template in SendGrid
    message.template_id = "d-5f87a7f6603b44e09b21cfdcf6514ffa"
    message.merge_data = {
        recipient.email: {
            "userName": recipient.first_name or recipient.email.split("@")[0],
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
    return message
