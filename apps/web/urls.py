from django.conf import settings
from django.urls import path
from django.views.generic import TemplateView

from . import frames, views

app_name = "web"

urlpatterns = [
    # site
    path("", views.Home.as_view(), name="home"),
    path("pricing", views.Pricing.as_view(), name="pricing"),
    path("about", views.About.as_view(), name="about"),
    path("legal/privacy-policy", views.PrivacyPolicy.as_view(), name="privacy-policy"),
    path("legal/terms-of-use", views.TermsOfUse.as_view(), name="terms-of-use"),
    # app
    path("toggle-sidebar", views.toggle_sidebar),
    # frames
    path("help", frames.HelpModal.as_view(), name="help"),
    path("changelog", frames.ChangelogModal.as_view(), name="changelog"),
]

# Users should not be able to access error pages directly.
if settings.DEBUG:
    urlpatterns += [
        path("404", TemplateView.as_view(template_name="404.html"), name="404"),
        path("500", TemplateView.as_view(template_name="500.html"), name="500"),
    ]
