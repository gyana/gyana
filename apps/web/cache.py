from django.views.decorators.cache import cache_page

SITE_CACHE_TIMEOUT = 60 * 15  # 15 minutes


def cache_site(view):
    return cache_page(SITE_CACHE_TIMEOUT)
