from functools import cache

import yaml
from django.conf import settings
from django.template import Context, Template

CONTENT_ROOT = "apps/web/content"


def get_content(path, context=None):
    content = open(f"{CONTENT_ROOT}/{path}")

    if context:
        content = Template(content.read()).render(Context(context))

    return yaml.safe_load(content)


if not settings.DEBUG:
    get_content = cache(get_content)
