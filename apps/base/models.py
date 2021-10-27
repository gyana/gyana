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
        return getattr(self, "node") or self.widget
