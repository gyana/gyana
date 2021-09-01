from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _

from apps.appsumo.config import APPSUMO_MAX_STACK, APPSUMO_PLANS
from apps.base.models import BaseModel

from . import roles

DEFAULT_ROW_LIMIT = 1_000_000
WARNING_BUFFER = 0.2


class Team(BaseModel):
    name = models.CharField(max_length=100)

    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="teams", through="Membership"
    )

    override_row_limit = models.BigIntegerField(null=True)
    # row count is recalculated on a daily basis, or re-counted in certain situations
    # calculating every view is too expensive
    row_count = models.BigIntegerField(default=0)
    row_count_calculated = models.DateTimeField(null=True)

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
    def row_limit(self):
        if self.override_row_limit is not None:
            return self.override_row_limit

        active_codes = self.appsumocode_set.filter(refunded_before=None).all()
        stacked = len(active_codes)

        if stacked == 0:
            return DEFAULT_ROW_LIMIT

        # to determine your plan, take the most recently purchased code
        most_recent = max(
            (
                code.purchased_before
                for code in active_codes
                if code.purchased_before is not None
            ),
            default=timezone.now(),
        )
        best_plan = next(
            plan for expired, plan in APPSUMO_PLANS.items() if expired >= most_recent
        )
        rows = best_plan.get(min(stacked, APPSUMO_MAX_STACK))["rows"]

        # extra 1M for writing a review
        if hasattr(self, "appsumoreview"):
            rows += 1_000_000

        return rows

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
