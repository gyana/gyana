from django.shortcuts import get_object_or_404

from apps.base.access import login_and_permission_to_access
from apps.teams.access import user_is_member

from .models import CName


def cname_of_project(user, pk, *args, **kwargs):
    cname = get_object_or_404(CName, pk=pk)
    return user_is_member(user, cname.team.id)


login_and_cname_required = login_and_permission_to_access(cname_of_project)
