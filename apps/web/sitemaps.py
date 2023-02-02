from django.contrib import sitemaps
from django.urls import reverse

from .urls import sitmap_urlpatterns
from .views import USE_CASES


class WebSitemap(sitemaps.Sitemap):
    priority = 0.5
    changefreq = "daily"

    def items(self):
        return [f"web:{pattern.name}" for pattern in sitmap_urlpatterns]

    def location(self, item):
        return reverse(item)


class IntegrationsSitemap(sitemaps.Sitemap):
    priority = 0.5
    changefreq = "daily"

    def location(self, item):
        return item


class UseCaseSitemap(sitemaps.Sitemap):
    priority = 0.5
    changefreq = "daily"

    def location(self, item):
        return item
