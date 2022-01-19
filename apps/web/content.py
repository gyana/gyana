from functools import cache

import yaml
from django.conf import settings

CONTENT_ROOT = "apps/web/content"


def get_content(path):
    return yaml.load(open(f"{CONTENT_ROOT}/{path}", "r"))


if not settings.DEBUG:
    get_content = cache(get_content)
