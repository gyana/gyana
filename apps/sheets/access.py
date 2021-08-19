from apps.base.access import login_and_permission_to_access
from apps.sheets.models import Sheet
from apps.teams.roles import user_can_access_team
from django.shortcuts import get_object_or_404


def sheet_of_team(user, pk, *args, **kwargs):
    sheet = get_object_or_404(Sheet, pk=pk)
    return user_can_access_team(user, sheet.integration.project.team)


login_and_sheet_required = login_and_permission_to_access(sheet_of_team)
