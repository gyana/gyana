from dirtyfields import DirtyFieldsMixin
from django.db import models
from django.utils import timezone
from model_clone import CloneMixin


class BaseModel(models.Model):
    """
    Base model that includes default created / updated timestamps.
    """

    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        abstract = True
        ordering = ("-updated",)


class SaveParentModel(DirtyFieldsMixin, CloneMixin, BaseModel):
    class Meta:
        abstract = True

    def save(self, *args, **kwargs) -> None:
        if self.is_dirty():
            self.parent.data_updated = timezone.now()
            self.parent.save()
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.parent.data_updated = timezone.now()
        self.parent.save()
        return super().delete(*args, **kwargs)

    @property
    def parent(self):
        if hasattr(self, "node") and (node := getattr(self, "node")):
            return node
        return self.widget


class SchedulableModel(BaseModel):
    class Meta(BaseModel.Meta):
        abstract = True

    # currently ignored in connectors
    is_scheduled = models.BooleanField(default=False)
    succeeded_at = models.DateTimeField(null=True)
    failed_at = models.DateTimeField(null=True)

    @property
    def _project(self):
        return (
            self.integration.project if hasattr(self, "integration") else self.project
        )

    @property
    def up_to_date(self):

        latest = self._project.latest_schedule

        just_failed = self.failed_at is not None and self.failed_at > latest
        just_succeeded = self.succeeded_at is not None and self.succeeded_at > latest

        return just_failed or just_succeeded

    def run_for_schedule(self):
        raise NotImplementedError

    @property
    def succeeded(self):
        return self.succeeded_at is not None and (
            self.failed_at is None or self.succeeded_at > self.failed_at
        )
