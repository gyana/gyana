from apps.integrations.models import Integration
from apps.teams.roles import user_can_access_team
from apps.base.access import login_and_permission_to_access
from django.shortcuts import get_object_or_404


def integration_of_team(user, pk, *args, **kwargs):
    integration = get_object_or_404(Integration, pk=pk)
    return user_can_access_team(user, integration.project.team)


login_and_integration_required = login_and_permission_to_access(integration_of_team)
