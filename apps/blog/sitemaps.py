from django.contrib import sitemaps
from django.urls import reverse

from .models import Post


class BlogSitemap(sitemaps.Sitemap):
    priority = 0.5
    changefreq = "daily"

    def items(self):
        return [reverse("blog:list")] + [
            reverse("blog:detail", args=(post.slug,)) for post in Post.objects.all()
        ]

    def location(self, item):
        return item
