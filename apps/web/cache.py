from django.views.decorators.cache import cache_page

SITE_CACHE_TIMEOUT = 60 * 15  # 15 minutes

cache_site = cache_page(SITE_CACHE_TIMEOUT, cache="site")
