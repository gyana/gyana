from django.conf import settings
from django.urls import path
from django.views.generic import TemplateView

from . import frames, views
from .cache import cache_site

app_name = "web"

sitmap_urlpatterns = [
    path("", views.Home.as_view(), name="home"),  # cache_site in view.get
    path("pricing", cache_site(views.Pricing.as_view()), name="pricing"),
    path("integrations", cache_site(views.Integrations.as_view()), name="integrations"),
    path("about", cache_site(views.About.as_view()), name="about"),
    path(
        "privacy-policy",
        cache_site(views.PrivacyPolicy.as_view()),
        name="privacy-policy",
    ),
    path("terms-of-use", cache_site(views.TermsOfUse.as_view()), name="terms-of-use"),
]

urlpatterns = sitmap_urlpatterns + [
    path("toggle-sidebar", views.toggle_sidebar),
    # frames
    path(
        "demo/integrations", frames.IntegrationsDemo.as_view(), name="integrations-demo"
    ),
    path(
        "demo/search-integrations",
        frames.SearchIntegrationsDemo.as_view(),
        name="search-integrations-demo",
    ),
    path("demo/workflows", frames.WorkflowsDemo.as_view(), name="workflows-demo"),
    path("demo/dashboards", frames.DashboardsDemo.as_view(), name="dashboards-demo"),
    path("demo/support", frames.SupportDemo.as_view(), name="support-demo"),
    path("demo/intercom", frames.IntercomDemo.as_view(), name="intercom-demo"),
    path("help", frames.HelpModal.as_view(), name="help"),
    path("changelog", frames.ChangelogModal.as_view(), name="changelog"),
]

# Users should not be able to access error pages directly.
if settings.DEBUG:
    urlpatterns += [
        path("404", TemplateView.as_view(template_name="404.html"), name="404"),
        path("500", TemplateView.as_view(template_name="500.html"), name="500"),
    ]
