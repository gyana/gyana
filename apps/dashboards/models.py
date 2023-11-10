from uuid import uuid4

from django.conf import settings
from django.contrib.auth import password_validation
from django.contrib.auth.hashers import (
    check_password,
    is_password_usable,
    make_password,
)
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.db.models import Deferrable, UniqueConstraint
from django.urls import reverse
from django.utils.translation import gettext_lazy

from apps.base.models import BaseModel, HistoryModel
from apps.projects.models import Project

from .utils import getDefaultThemePalette


class DashboardSettings(models.Model):
    class Meta:
        abstract = True

    class Category(models.TextChoices):
        GENERAL = "general", "General"
        WIDGET = "widget", "Widget"
        CANVAS = "canvas", "Canvas"
        ADVANCED = "advanced", "Advanced"

    class FontFamily(models.TextChoices):
        BOOGALOO = "Boogaloo"
        LATO = "Lato"
        MERRIWEATHER = "Merriweather"
        MONTSERRAT = "Montserrat"
        OPEN_SANS = "Open Sans"
        ROBOTO = "Roboto"
        UBUNTU = "Ubuntu"

    extra_html_head = models.TextField(null=True)
    extra_css = models.TextField(null=True)
    preview_by_default = models.BooleanField(default=False)
    grid_size = models.IntegerField(default=15)
    width = models.IntegerField(default=1200)
    height = models.IntegerField(default=840)
    palette_colors = ArrayField(
        models.CharField(default="#5D62B5", max_length=7),
        size=10,
        default=getDefaultThemePalette,
    )
    background_color = models.CharField(default="#ffffff", max_length=7)
    font_size = models.IntegerField(default="14")
    font_color = models.CharField(default="#242733", max_length=7)
    font_family = models.CharField(
        max_length=30, default=FontFamily.ROBOTO, choices=FontFamily.choices
    )
    snap_to_grid = models.BooleanField(default=True)

    show_widget_border = models.BooleanField(default=True)
    show_widget_headers = models.BooleanField(default=True)
    widget_header_font_size = models.IntegerField(default="18")
    widget_background_color = models.CharField(default="#ffffff", max_length=7)
    widget_border_color = models.CharField(default="#e6e6e6", max_length=7)
    widget_border_radius = models.IntegerField(default=5)
    widget_border_thickness = models.IntegerField(default=1)


class Dashboard(DashboardSettings, HistoryModel):
    class SharedStatus(models.TextChoices):
        PRIVATE = "private", "Private"
        PUBLIC = "public", "Public"
        PASSWORD_PROTECTED = "password_protected", "Password Protected"

    name = models.CharField(max_length=255, default="Untitled")
    project = models.ForeignKey(Project, on_delete=models.CASCADE)
    shared_status = models.CharField(
        max_length=20, default=SharedStatus.PRIVATE, choices=SharedStatus.choices
    )
    shared_id = models.UUIDField(null=True, blank=True, unique=True)
    password = models.CharField(gettext_lazy("password"), max_length=128, null=True)
    password_set = models.DateTimeField(null=True, editable=False)

    # Stores the raw password if set_password() is called so that it can
    # be passed to password_changed() after the model is saved.
    _password = None

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        if self.preview_by_default:
            return "%s?mode=view" % (
                reverse("project_dashboards:detail", args=(self.project.id, self.id))
            )

        return reverse("project_dashboards:detail", args=(self.project.id, self.id))

    def save(self, *args, **kwargs):
        is_creation = self.id is None
        skip_dashboard_update = kwargs.pop("skip_dashboard_update", False)
        super().save(*args, **kwargs)

        if not is_creation and not skip_dashboard_update:
            self.updates.create(content_object=self)
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
    def is_shared(self):
        return self.shared_status in [
            self.SharedStatus.PUBLIC,
            self.SharedStatus.PASSWORD_PROTECTED,
        ]

    @property
    def public_url(self):
        domain = settings.EXTERNAL_URL
        return f"{domain}/dashboards/{self.shared_id}"

    @property
    def widgets(self):
        from apps.widgets.models import Widget

        return Widget.objects.filter(page__dashboard=self).all()

    @property
    def widget_history(self):
        from apps.widgets.models import Widget

        return Widget.history.filter(page__dashboard=self).all()

    @property
    def page_set(self):
        return Page.objects.filter(dashboard=self).all()

    def make_clone(self, attrs=None, sub_clone=False, using=None):
        if self.shared_id:
            attrs["shared_id"] = uuid4()
        return super().make_clone(attrs, sub_clone, using)

    @property
    def input_tables_fk(self):
        return [widget.table.id for widget in self.widgets.filter(table__isnull=False)]


class Page(HistoryModel):
    class Meta:
        ordering = ("position",)
        constraints = [
            UniqueConstraint(
                name="dashboards_page_dashboard_id_position",
                fields=["dashboard", "position"],
                deferrable=Deferrable.DEFERRED,
            )
        ]

    name = models.CharField(max_length=255, null=True)
    dashboard = models.ForeignKey(
        Dashboard, on_delete=models.CASCADE, related_name="pages"
    )
    position = models.IntegerField(default=1)

    @property
    def has_control(self):
        return hasattr(self, "control")

    def get_absolute_url(self):
        return f'{reverse("project_dashboards:detail", args=(self.dashboard.project.id, self.dashboard.id))}?dashboardPage={self.position}'

    def save(self, **kwargs) -> None:
        is_first_page = self.id is None and self.dashboard.pages.count() == 0
        skip_dashboard_update = kwargs.pop("skip_dashboard_update", False)
        super().save(**kwargs)
        if not skip_dashboard_update:
            # for the first page of a dashboard we want it to reflect the dashboard creation
            self.dashboard.updates.create(
                content_object=self if not is_first_page else self.dashboard
            )

    def delete(self, **kwargs):
        skip_dashboard_update = kwargs.pop("skip_dashboard_update", False)

        if not skip_dashboard_update:
            self.dashboard.updates.create(content_object=self)

        result = super().delete(**kwargs)

        for follow_page in self.dashboard.pages.filter(
            position__gt=self.position
        ).iterator():
            follow_page.position = follow_page.position - 1
            follow_page.save()

        return result

    def __str__(self) -> str:
        return f"Page {self.position}{f': {self.name}' if self.name else ''}"


# The DashboardVersion links to the dashboard model and we will be using the creation date
# For the other models. Hopefully, this is robust even in the event of children not
# propagating their update to their parents.
class DashboardVersion(BaseModel):
    dashboard = models.ForeignKey(
        Dashboard, on_delete=models.CASCADE, related_name="versions"
    )
    name = models.CharField(max_length=255, null=True, blank=True)


class DashboardUpdate(BaseModel):
    dashboard = models.ForeignKey(
        Dashboard, on_delete=models.CASCADE, related_name="updates"
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    content_object = GenericForeignKey("content_type", "object_id")


DASHBOARD_SETTING_TO_CATEGORY = {
    "extra_html_head": Dashboard.Category.ADVANCED,
    "extra_css": Dashboard.Category.ADVANCED,
    "preview_by_default": Dashboard.Category.GENERAL,
    "grid_size": Dashboard.Category.CANVAS,
    "width": Dashboard.Category.CANVAS,
    "height": Dashboard.Category.CANVAS,
    "snap_to_grid": Dashboard.Category.CANVAS,
    "palette_colors": Dashboard.Category.GENERAL,
    "background_color": Dashboard.Category.GENERAL,
    "font_size": Dashboard.Category.GENERAL,
    "font_color": Dashboard.Category.GENERAL,
    "font_family": Dashboard.Category.GENERAL,
    "show_widget_border": Dashboard.Category.GENERAL,
    "show_widget_headers": Dashboard.Category.WIDGET,
    "widget_header_font_size": Dashboard.Category.WIDGET,
    "widget_background_color": Dashboard.Category.WIDGET,
    "widget_border_color": Dashboard.Category.WIDGET,
    "widget_border_radius": Dashboard.Category.WIDGET,
    "widget_border_thickness": Dashboard.Category.WIDGET,
}
