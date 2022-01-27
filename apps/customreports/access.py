from rest_framework.generics import get_object_or_404

from apps.base.access import login_and_permission_to_access
from apps.connectors.models import Connector
from apps.projects.access import user_can_access_project


def customreport_of_project(user, connector_id, *args, **kwargs):
    connector = get_object_or_404(Connector, pk=connector_id)
    return user_can_access_project(user, connector.integration.project)


login_and_customreport_required = login_and_permission_to_access(
    customreport_of_project
)
