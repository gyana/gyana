from rest_framework.generics import get_object_or_404

from apps.base.access import login_and_permission_to_access
from apps.connectors.models import Connector
from apps.teams.roles import user_can_access_team


def connector_of_team(user, pk, *args, **kwargs):
    connector = get_object_or_404(Connector, pk=pk)
    return user_can_access_team(user, connector.integration.project.team)


login_and_connector_required = login_and_permission_to_access(connector_of_team)
