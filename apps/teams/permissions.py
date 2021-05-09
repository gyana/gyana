from rest_framework import permissions

from apps.teams.roles import is_admin, is_member


class TeamAccessPermissions(permissions.BasePermission):
    """
    Object-level permission to only allow admins of a team to edit it.
    """

    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any request
        # so we'll always allow GET, HEAD or OPTIONS requests for members
        if request.method in permissions.SAFE_METHODS:
            return is_member(request.user, obj)

        return is_admin(request.user, obj)


class TeamModelAccessPermissions(permissions.BasePermission):
    """
    Object-level permission to only allow admins of a team to
    edit the underlying object.
    Assumes the model instance has a `team` attribute.
    """

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return is_member(request.user, obj.team)

        return is_admin(request.user, obj.team)
