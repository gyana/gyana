from django.db import models
from django.urls import reverse

from apps.base.models import BaseModel


class OAuth2(BaseModel):
    name = models.CharField(max_length=255)
    project = models.ForeignKey("projects.Project", on_delete=models.CASCADE)

    # oauth2 configuration from the user
    client_id = models.CharField(max_length=1024)
    client_secret = models.CharField(max_length=1024)
    authorization_base_url = models.URLField(max_length=2048)
    token_url = models.URLField(max_length=2048)
    scope = models.CharField(max_length=1024, blank=True)

    # derived from the server
    state = models.CharField(max_length=1024, null=True)
    token = models.JSONField(null=True)

    def is_authorized(self):
        return self.token is not None

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse("project_oauth2:update", args=(self.project.id, self.id))
