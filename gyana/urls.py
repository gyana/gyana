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
from apps.dashboards import urls as dashboard_urls
from apps.integrations import urls as integration_urls
from apps.projects import urls as project_urls
from apps.subscriptions.urls import team_urlpatterns as subscriptions_team_urls
from apps.widgets import urls as widget_urls
from apps.workflows import urls as workflow_urls
from django.conf import settings
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path
from rest_framework.documentation import get_schemajs_view, include_docs_urls

schemajs_view = get_schemajs_view(title="API")

# urls that are unique to using a team should go here
team_urlpatterns = [
    path("subscription/", include(subscriptions_team_urls)),
    path("team/projects/", include(project_urls.team_urlpatterns)),
]

# urls that are scoped within a project
project_urlpatterns = [
    path("", include("apps.projects.urls")),
    path(
        "<int:project_id>/integrations/", include(integration_urls.project_urlpatterns)
    ),
    path("<int:project_id>/workflows/", include(workflow_urls.project_urlpatterns)),
    path("<int:project_id>/dashboards/", include(dashboard_urls.project_urlpatterns)),
    path(
        "<int:project_id>/dashboards/<int:dashboard_id>/widgets/",
        include(widget_urls.dashboard_urlpatterns),
    ),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("a/<slug:team_slug>/", include(team_urlpatterns)),
    path("accounts/", include("turbo_allauth.urls")),
    path("users/", include("apps.users.urls")),
    path("filters/", include("apps.filters.urls")),
    path("subscriptions/", include("apps.subscriptions.urls")),
    path("teams/", include("apps.teams.urls")),
    path("projects/", include(project_urlpatterns)),
    path("integrations/", include("apps.integrations.urls")),
    path("workflows/", include("apps.workflows.urls")),
    path("dashboards/", include("apps.dashboards.urls")),
    path("widgets/", include("apps.widgets.urls")),
    path("tables/", include("apps.tables.urls")),
    # path("invites/", include("apps.invites.urls")),
    path("invitations/", include("invitations.urls")),
    path("", include("apps.web.urls")),
    path("celery-progress/", include("celery_progress.urls")),
    # API docs
    # these are needed for schema.js
    path("docs/", include_docs_urls(title="API Docs")),
    path("schemajs/", schemajs_view, name="api_schemajs"),
    # djstripe urls - for webhooks
    path("stripe/", include("djstripe.urls", namespace="djstripe")),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
