from dirtyfields import DirtyFieldsMixin
from django.conf import settings
from django.db import models
from django.urls import reverse
from django.utils import timezone
from safedelete.models import SafeDeleteModel
from storages.backends.gcloud import GoogleCloudStorage
from timezone_field import TimeZoneField
from timezone_field.choices import with_gmt_offset

from apps.base.clients import get_engine
from apps.base.models import BaseModel

from . import roles
from .flag import Flag  # noqa
from .utils import getRandomColor


class Team(DirtyFieldsMixin, BaseModel, SafeDeleteModel):
    class Meta:
        ordering = ("-created",)

    icon = models.FileField(
        storage=GoogleCloudStorage(
            bucket_name=settings.GS_PUBLIC_BUCKET_NAME,
            cache_control=settings.GS_PUBLIC_CACHE_CONTROL,
            querystring_auth=False,
        ),
        upload_to="team-icons/",
        null=True,
        blank=True,
    )
    color = models.CharField(default=getRandomColor, max_length=7)
    name = models.CharField(max_length=100)

    members = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="teams", through="Membership"
    )

    override_row_limit = models.BigIntegerField(null=True, blank=True)
    override_credit_limit = models.BigIntegerField(null=True, blank=True)
    override_rows_per_integration_limit = models.BigIntegerField(null=True, blank=True)

    # row count is recalculated on a daily basis, or re-counted in certain situations
    # calculating every view is too expensive
    row_count = models.BigIntegerField(default=0)
    row_count_calculated = models.DateTimeField(null=True)

    timezone = TimeZoneField(default="GMT", choices_display="WITH_GMT_OFFSET")
    has_free_trial = models.BooleanField(default=False)

    def save(self, *args, **kwargs):
        create = not self.pk
        super().save(*args, **kwargs)
        if create:
            get_engine().create_team_dataset(self)

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
    def timezone_with_gtm_offset(self):
        return with_gmt_offset([self.timezone])[0][1]

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
    def admins(self):
        return self.members.filter(membership__role=roles.ROLE_ADMIN)

    def add_new_rows(self, num_rows):
        return num_rows + self.row_count

    def update_daily_sync_time(self):
        for project in self.project_set.all():
            project.update_schedule()


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
