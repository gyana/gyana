from django.db import models
from django.urls import reverse


class {{ cookiecutter.model_name }}(models.Model):
    name = models.CharField(max_length=255)
    created = models.DateTimeField(auto_now_add=True, editable=False)
    updated = models.DateTimeField(auto_now=True, editable=False)

    class Meta:
        ordering = ('-created', )

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("{{ cookiecutter.app_name }}:detail", args=(self.pk, ))
