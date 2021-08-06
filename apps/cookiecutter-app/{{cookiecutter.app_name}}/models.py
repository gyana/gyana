from apps.base.models import BaseModel
from django.db import models
from django.urls import reverse


class {{ cookiecutter.model_name }}(BaseModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("{{ cookiecutter.app_name }}:detail", args=(self.pk, ))
