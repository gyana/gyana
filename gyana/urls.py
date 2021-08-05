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

from apps.base.converters import HashIdConverter
from django.conf import settings
from django.conf.urls import url
from django.conf.urls.static import static
from django.contrib import admin
from django.urls import include, path, register_converter
from django.urls.converters import IntConverter
from rest_framework.documentation import get_schemajs_view, include_docs_urls

register_converter(HashIdConverter if settings.USE_HASHIDS else IntConverter, "hashid")

from apps.dashboards import urls as dashboard_urls
from apps.integrations import urls as integration_urls
from apps.invites import urls as invite_urls
from apps.nodes import urls as node_urls
from apps.projects import urls as project_urls
from apps.tables import urls as tables_urls
from apps.teams import urls as team_urls
from apps.widgets import urls as widget_urls
from apps.workflows import urls as workflow_urls

schemajs_view = get_schemajs_view(title="API")

# urls that are scoped within a project
project_urlpatterns = [
    path("", include("apps.projects.urls")),
    path(
        "<hashid:project_id>/integrations/",
        include(integration_urls.project_urlpatterns),
    ),
    path("<hashid:project_id>/workflows/", include(workflow_urls.project_urlpatterns)),
    path(
        "<hashid:project_id>/dashboards/", include(dashboard_urls.project_urlpatterns)
    ),
    path("<hashid:project_id>/tables/", include(tables_urls.project_urlpatterns)),
    path(
        "<hashid:project_id>/dashboards/<hashid:dashboard_id>/widgets/",
        include(widget_urls.dashboard_urlpatterns),
    ),
]

teams_urlpatterns = [
    path("", include("apps.teams.urls")),
    path("<hashid:team_id>/invites/", include(invite_urls.team_urlpatterns)),
    path("<hashid:team_id>/projects/", include(project_urls.team_urlpatterns)),
    path("<hashid:team_id>/members", include(team_urls.membership_urlpatterns)),
]


urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("turbo_allauth.urls")),
    path("users/", include("apps.users.urls")),
    path("filters/", include("apps.filters.urls")),
    path("teams/", include(teams_urlpatterns)),
    path("projects/", include(project_urlpatterns)),
    path("integrations/", include("apps.integrations.urls")),
    path("workflows/", include("apps.workflows.urls")),
    path("workflows/<int:workflow_id>/", include(node_urls.workflow_urlpatterns)),
    path("dashboards/", include("apps.dashboards.urls")),
    path("widgets/", include("apps.widgets.urls")),
    path("invitations/", include("invitations.urls")),
    path("nodes/", include("apps.nodes.urls")),
    path("", include("apps.web.urls")),
    path("celery-progress/", include("celery_progress.urls")),
    # API docs
    # these are needed for schema.js
    path("docs/", include_docs_urls(title="API Docs")),
    path("schemajs/", schemajs_view, name="api_schemajs"),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.CYPRESS_URLS:
    urlpatterns += [
        path("cypress/", include("apps.base.cypress_urls")),
    ]
