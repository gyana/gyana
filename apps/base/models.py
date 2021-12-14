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

    @property
    def entity_id(self):
        # A unique identifier for this entity across all models
        return f"{self._meta.db_table}-{self.id}"


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
