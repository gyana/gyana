from apps.integrations.emails import integration_ready_email
from celery import shared_task
from django.shortcuts import get_object_or_404

from .models import Integration


@shared_task(bind=True)
def send_integration_email(self, integration_id: int):
    integration = get_object_or_404(Integration, pk=integration_id)

    email = integration_ready_email(integration, integration.created_by)
    email.send()

    return integration_id
