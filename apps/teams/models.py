from functools import cached_property

from apps.base.models import BaseModel
from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _

from . import roles

DEFAULT_ROW_LIMIT = 1_000_000


class Team(BaseModel):
    """
    A Team, with members.
    """

    name = models.CharField(max_length=100)

    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="teams", through="Membership"
    )

    row_limit = models.BigIntegerField(default=DEFAULT_ROW_LIMIT)

    @cached_property
    def num_rows(self):
        from apps.tables.models import Table

        return (
            Table.available.filter(integration__project__team=self).aggregate(
                models.Sum("num_rows")
            )["num_rows__sum"]
            or 0
        )

    def __str__(self):
        return self.name


class Membership(BaseModel):
    """
    A user's team membership
    """

    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=100, choices=roles.ROLE_CHOICES)
