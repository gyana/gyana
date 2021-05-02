"""Gyana URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework.documentation import get_schemajs_view, include_docs_urls

schemajs_view = get_schemajs_view(title="API")


urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("turbo_allauth.urls")),
    path("users/", include("apps.users.urls")),
    path("subscriptions/", include("apps.subscriptions.urls")),
    path("teams/", include("apps.teams.urls")),
    path("datasets/", include("apps.datasets.urls")),
    path("dataflows/", include("apps.dataflows.urls")),
    path("dashboards/", include("apps.dashboards.urls")),
    path("widgets/", include("apps.widgets.urls")),
    path("", include("apps.web.urls")),
    path("pegasus/", include("pegasus.apps.examples.urls")),
    path("celery-progress/", include("celery_progress.urls")),
    # API docs
    # these are needed for schema.js
    path("docs/", include_docs_urls(title="API Docs")),
    path("schemajs/", schemajs_view, name="api_schemajs"),
    # djstripe urls - for webhooks
    path("stripe/", include("djstripe.urls", namespace="djstripe")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
