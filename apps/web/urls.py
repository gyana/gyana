from django.conf import settings
from django.urls import path
from django.views.generic import TemplateView

from . import views

app_name = "web"
urlpatterns = [
    path("", views.home, name="home"),
]

# Users should not be able to access error pages directly.
if settings.DEBUG:
    urlpatterns += [
        path("404", TemplateView.as_view(template_name="404.html"), name="404"),
        path("500", TemplateView.as_view(template_name="500.html"), name="500"),
    ]