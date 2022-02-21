from django.shortcuts import get_object_or_404

from apps.base.access import login_and_permission_to_access
from apps.projects.access import user_can_access_project
from apps.sheets.models import Sheet


def sheet_of_team(user, pk, *args, **kwargs):
    sheet = get_object_or_404(Sheet, pk=pk)
    return user_can_access_project(user, sheet.integration.project)


login_and_sheet_required = login_and_permission_to_access(sheet_of_team)
