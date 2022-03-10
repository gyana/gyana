from dirtyfields import DirtyFieldsMixin
from django.db import models
from django.utils import timezone
from simple_history.models import HistoricalRecords

from .clone import CloneMixin


class BaseModel(CloneMixin, models.Model):
    """
    Base model that includes default created / updated timestamps.
    """

    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        abstract = True
        ordering = ("-updated",)

    @property
    def entity_id(self):
        # A unique identifier for this entity across all models
        return f"{self._meta.db_table}-{self.id}"


class HistoryModel(BaseModel):
    class Meta:
        abstract = True

    history = HistoricalRecords(inherit=True)

    def restore_as_of(self, as_of):
        """Restores historic version as existed at `as_of` and it's downstream relations."""
        self.history.as_of(as_of).save()

        for f in self._meta.related_objects:
            if f.one_to_many and hasattr(f.related_model, "history"):
                to_restore = (
                    f.related_model.history.as_of(as_of)
                    .filter(**{f.remote_field.name: self})
                    .all()
                )

                for instance in to_restore:
                    instance.restore_as_of(as_of)
                for instance in (
                    getattr(self, f.get_accessor_name())
                    .exclude(id__in=to_restore.values_list("id"))
                    .all()
                ):
                    instance.delete()
            if f.one_to_one and hasattr(f.related_model, "history"):
                if instance := (
                    f.related_model.history.as_of(as_of)
                    .filter(**{f.remote_field.name: self})
                    .first()
                ):
                    instance.restore_as_of(as_of)

            # TODO: Many to many


class SaveParentModel(DirtyFieldsMixin, HistoryModel):
    class Meta:
        abstract = True
        ordering = ("created",)

    _clone_excluded_m2o_or_o2m_fields = ["widget", "node"]

    def save(self, *args, **kwargs) -> None:
        if self.is_dirty():
            self.parent.data_updated = timezone.now()
            if hasattr(self.parent, "history"):
                self.parent.save_without_historical_record()
            else:
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
