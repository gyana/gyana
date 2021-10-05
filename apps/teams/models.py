from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone

from apps.base.models import BaseModel

from . import roles
from .config import PLANS

WARNING_BUFFER = 0.2


class Team(BaseModel):
    icon = models.FileField(upload_to="team-icons/", null=True, blank=True)
    name = models.CharField(max_length=100)

    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="teams", through="Membership"
    )

    override_row_limit = models.BigIntegerField(null=True, blank=True)
    # row count is recalculated on a daily basis, or re-counted in certain situations
    # calculating every view is too expensive
    row_count = models.BigIntegerField(default=0)
    row_count_calculated = models.DateTimeField(null=True)

    def save(self, *args, **kwargs):
        from .bigquery import create_team_dataset

        create = not self.pk
        super().save(*args, **kwargs)
        if create:
            create_team_dataset(self)

    def update_row_count(self):
        from apps.tables.models import Table

        self.row_count = (
            Table.available.filter(integration__project__team=self).aggregate(
                models.Sum("num_rows")
            )["num_rows__sum"]
            or 0
        )
        self.row_count_calculated = timezone.now()
        self.save()

    @property
    def warning(self):
        return self.row_limit < self.row_count <= self.row_limit * (1 + WARNING_BUFFER)

    @property
    def enabled(self):
        return self.row_count <= self.row_limit * (1 + WARNING_BUFFER)

    @property
    def tables_dataset_id(self):
        from apps.base.clients import SLUG

        dataset_id = f"team_{self.id:06}_tables"
        if SLUG:
            dataset_id = f"{SLUG}_{dataset_id}"
        return dataset_id

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("teams:detail", args=(self.id,))

    @property
    def redeemed_codes(self):
        return self.appsumocode_set.count()

    @property
    def active_codes(self):
        return self.appsumocode_set.filter(refunded_before__isnull=True).count()

    @property
    def refunded_codes(self):
        return self.appsumocode_set.filter(refunded_before__isnull=False).count()

    @property
    def ltd_disabled(self):
        return self.active_codes == 0

    @property
    def exceeds_stacking_limit(self):
        return self.active_codes > 5

    @property
    def has_extra_rows(self):
        return self.appsumoextra_set.count() > 0

    @property
    def plan(self):
        from apps.appsumo.account import get_deal

        if self.active_codes > 0:
            return {**PLANS["appsumo"], **get_deal(self.appsumocode_set.all())}

        return PLANS["free"]

    @property
    def row_limit(self):
        from .account import get_row_limit

        return get_row_limit(self)

    @property
    def credits(self):
        from .account import get_credits

        return get_credits(self)

    @property
    def total_members(self):
        return self.members.count()

    @property
    def total_projects(self):
        return self.project_set.count()

    @property
    def total_invite_only_projects(self):
        from apps.projects.models import Project

        return self.project_set.filter(access=Project.Access.INVITE_ONLY).count()

    @property
    def can_create_project(self):
        if self.plan["projects"] == -1:
            return True
        return self.total_projects < self.plan["projects"]

    @property
    def can_create_invite_only_project(self):
        sub_accounts = self.plan.get("sub_accounts")

        if sub_accounts is None:
            return False
        if sub_accounts == -1:
            return True
        return self.total_invite_only_projects < sub_accounts

    @property
    def admins(self):
        return self.members.filter(membership__role=roles.ROLE_ADMIN)


class Membership(BaseModel):
    """
    A user's team membership
    """

    team = models.ForeignKey(Team, on_delete=models.CASCADE)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE)
    role = models.CharField(max_length=100, choices=roles.ROLE_CHOICES)

    @property
    def can_delete(self):
        return self.team.admins.exclude(id=self.user.id).count() > 0
