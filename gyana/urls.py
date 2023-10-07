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
from wagtail.admin import urls as wagtailadmin_urls
from wagtail.contrib.sitemaps import Sitemap as WagtailSitemap
from wagtail.core import urls as wagtail_urls
from wagtail.documents import urls as wagtaildocs_urls

from apps.base.converters import HashIdConverter

register_converter(HashIdConverter if settings.USE_HASHIDS else IntConverter, "hashid")


from wagtail.api.v2.views import PagesAPIViewSet

from apps.web.sitemaps import WebSitemap

PagesAPIViewSet.schema = None
schemajs_view = get_schemajs_view(title="API")


urlpatterns = [
    path("admin_tools/", include("admin_tools.urls")),
    path("admin/", admin.site.urls),
    path("learn/", include("apps.learn.urls")),
    path("", include("apps.web.urls")),
    path("celery-progress/", include("celery_progress.urls")),
    path("hijack/", include("hijack.urls", namespace="hijack")),
    # API docs
    # these are needed for schema.js
    path("docs/", include_docs_urls(title="API Docs")),
    path("schemajs/", schemajs_view, name="api_schemajs"),
    path("cms/", include(wagtailadmin_urls)),
    path("documents/", include(wagtaildocs_urls)),
    path(
        "sitemap.xml",
        sitemap,
        {"sitemaps": {"web": WebSitemap, "wagtail": WagtailSitemap}},
        name="django.contrib.sitemaps.views.sitemap",
    ),
]

if settings.DEBUG:
    urlpatterns += [path("silk/", include("silk.urls", namespace="silk"))]

urlpatterns += [
    path("", include(wagtail_urls)),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
