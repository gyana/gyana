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
from django.contrib.sitemaps.views import sitemap
from django.urls import include, path, register_converter
from django.urls.converters import IntConverter
from rest_framework.documentation import get_schemajs_view, include_docs_urls

from apps.base.converters import HashIdConverter

register_converter(HashIdConverter if settings.USE_HASHIDS else IntConverter, "hashid")

from apps.controls import urls as control_urls
from apps.customapis import urls as api_urls
from apps.dashboards import urls as dashboard_urls
from apps.integrations import urls as integration_urls
from apps.invites import urls as invite_urls
from apps.nodes import urls as node_urls
from apps.oauth2 import urls as oauth2_urls
from apps.projects import urls as project_urls
from apps.sheets import urls as sheet_urls
from apps.teams import urls as team_urls
from apps.uploads import urls as upload_urls
from apps.users import urls as users_urls
from apps.widgets import urls as widget_urls
from apps.workflows import urls as workflow_urls

schemajs_view = get_schemajs_view(title="API")


integration_urlpatterns = [
    path("", include(integration_urls.project_urlpatterns)),
    path("customapis/", include(api_urls.integration_urlpatterns)),
    path("sheets/", include(sheet_urls.integration_urlpatterns)),
    path("uploads/", include(upload_urls.integration_urlpatterns)),
]

# urls that are scoped within a project
project_urlpatterns = [
    path("", include("apps.projects.urls")),
    path("<hashid:project_id>/integrations/", include(integration_urlpatterns)),
    path("<hashid:project_id>/workflows/", include(workflow_urls.project_urlpatterns)),
    path(
        "<hashid:project_id>/dashboards/", include(dashboard_urls.project_urlpatterns)
    ),
    path("<hashid:project_id>/oauth2/", include(oauth2_urls.project_urlpatterns)),
    path(
        "<hashid:project_id>/dashboards/<hashid:dashboard_id>/widgets/",
        include(widget_urls.dashboard_urlpatterns),
    ),
    path(
        "<hashid:project_id>/dashboards/<hashid:dashboard_id>/controls/",
        include(control_urls.dashboard_urlpatterns),
    ),
]


teams_urlpatterns = [
    path("", include("apps.teams.urls")),
    path("<hashid:team_id>/invites/", include(invite_urls.team_urlpatterns)),
    path("<hashid:team_id>/projects/", include(project_urls.team_urlpatterns)),
    path("<hashid:team_id>/members/", include(team_urls.membership_urlpatterns)),
]


urlpatterns = [
    path("admin_tools/", include("admin_tools.urls")),
    path("admin/", admin.site.urls),
    path("exports/", include("apps.exports.urls")),
    path("controls/", include("apps.controls.urls")),
    path("users/", include("apps.users.urls")),
    path("filters/", include("apps.filters.urls")),
    path("teams/", include(teams_urlpatterns)),
    path("projects/", include(project_urlpatterns)),
    path("integrations/", include("apps.integrations.urls")),
    path("workflows/", include("apps.workflows.urls")),
    path("workflows/<int:pk>/", include(node_urls.workflow_urlpatterns)),
    path("dashboards/", include("apps.dashboards.urls")),
    path("widgets/", include("apps.widgets.urls")),
    path("invitations/", include("invitations.urls")),
    path("nodes/", include("apps.nodes.urls")),
    path("uploads/", include("apps.uploads.urls")),
    path("sheets/", include("apps.sheets.urls")),
    path("oauth2/", include("apps.oauth2.urls")),
    path("tables/", include("apps.tables.urls")),
    path("", include("apps.web.urls")),
    path("celery-progress/", include("celery_progress.urls")),
    path("hijack/", include("hijack.urls", namespace="hijack")),
    # API docs
    # these are needed for schema.js
    path("docs/", include_docs_urls(title="API Docs")),
    path("schemajs/", schemajs_view, name="api_schemajs"),
    path("", include(users_urls.accounts_urlpatterns)),
]

if settings.CYPRESS_URLS:
    urlpatterns += [
        path("cypress/", include("apps.cypress.urls")),
    ]

if settings.DEBUG:
    urlpatterns += [path("silk/", include("silk.urls", namespace="silk"))]

urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
