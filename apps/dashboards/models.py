from django.conf import settings
from django.contrib.auth import password_validation
from django.contrib.auth.hashers import (
    check_password,
    is_password_usable,
    make_password,
)
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy
from model_clone import CloneMixin

from apps.base.models import BaseModel
from apps.dateslicers.models import DateSlicer
from apps.projects.models import Project


# These were taken from fusioncharts.theme.fusion.js as the default values
# for a chart palette.
def getFusionThemePalette():
    return [
        "#5D62B5",
        "#29C3BE",
        "#F2726F",
        "#FFC533",
        "#62B58F",
        "#BC95DF",
        "#67CDF2",
    ]


class Dashboard(CloneMixin, BaseModel):
    class SharedStatus(models.TextChoices):
        PRIVATE = "private", "Private"
        PUBLIC = "public", "Public"
        PASSWORD_PROTECTED = "password_protected", "Password-protected"

    name = models.CharField(max_length=255, default="Untitled")
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    shared_status = models.CharField(
        max_length=20, default=SharedStatus.PRIVATE, choices=SharedStatus.choices
    )
    shared_id = models.UUIDField(null=True, blank=True)
    password = models.CharField(gettext_lazy("password"), max_length=128, null=True)
    password_set = models.DateTimeField(null=True, editable=False)
    width = models.IntegerField(default=1200)
    height = models.IntegerField(default=840)
    grid_size = models.IntegerField(default=15)

    palette_colors = ArrayField(
        models.CharField(default="#5D62B5", max_length=7),
        size=10,
        default=getFusionThemePalette,
    )
    background_color = models.CharField(default="#ffffff", max_length=7)

    date_slicer = models.OneToOneField(DateSlicer, on_delete=models.SET_NULL, null=True)

    _clone_m2o_or_o2m_fields = ["widget_set"]

    # Stores the raw password if set_password() is called so that it can
    # be passed to password_changed() after the model is saved.
    _password = None

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("project_dashboards:detail", args=(self.project.id, self.id))

    def save(self, *args, **kwargs):
        super().save(*args, **kwargs)
        if self._password is not None:
            password_validation.password_changed(self._password, self)
            self._password = None

    # Copied these methods from djangos AbstractUser
    def set_password(self, raw_password):
        self.password = make_password(raw_password)
        self._password = raw_password

    def check_password(self, raw_password):
        """
        Return a boolean of whether the raw_password was correct. Handles
        hashing formats behind the scenes.
        """

        def setter(raw_password):
            self.set_password(raw_password)
            # Password hash upgrades shouldn't be considered password changes.
            self._password = None
            self.save(update_fields=["password"])

        return check_password(raw_password, self.password, setter)

    def set_unusable_password(self):
        # Set a value that will never be a valid hash
        self.password = make_password(None)

    def has_usable_password(self):
        """
        Return False if set_unusable_password() has been called for this user.
        """
        return is_password_usable(self.password)

    @property
    def public_url(self):
        domain = (
            f"https://{self.project.cname.domain}"
            if self.project.cname is not None
            else settings.EXTERNAL_URL
        )
        return f"{domain}/dashboards/{self.shared_id}"
