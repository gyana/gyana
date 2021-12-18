from django.shortcuts import get_object_or_404

from apps.base.access import login_and_permission_to_access
from apps.customapis.models import CustomApi
from apps.projects.access import user_can_access_project


def customapi_of_team(user, pk, *args, **kwargs):
    customapi = get_object_or_404(CustomApi, pk=pk)
    return user_can_access_project(user, customapi.integration.project)


login_and_customapi_required = login_and_permission_to_access(customapi_of_team)
