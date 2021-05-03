from django.db import models


class Filter(models.Model):
    name = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        ordering = ('-created', )

    def __str__(self):
        return self.name
