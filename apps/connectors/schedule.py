from django.utils import timezone

from apps.base import clients
from apps.integrations.models import Integration
from apps.projects.models import Project

from .models import Connector


def run_scheduled_connectors(project: Project):

    for connector in Connector.objects.is_scheduled_in_project(project).all():
        if (
            not connector.fivetran_sync_started
            or connector.fivetran_sync_started < project.schedule.run_started_at
        ):
            yield connector.integration.schedule_node_id, "running"
            clients.fivetran().start_update_sync(connector)

            connector.fivetran_sync_started = timezone.now()
            connector.save()

            connector.integration.state = Integration.State.LOAD
            connector.integration.save()

        else:
            connector.sync_updates_from_fivetran()
