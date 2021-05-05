from urllib.parse import urlparse

from django.urls import resolve

from .models import Project


class ProjectMixin:
    @property
    def project(self):
        resolver_match = resolve(urlparse(self.request.META["HTTP_REFERER"]).path)
        return Project.objects.get(pk=resolver_match.kwargs["pk"])
