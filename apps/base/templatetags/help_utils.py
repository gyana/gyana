import functools
import json

from django import template

ARTICLES_PATH = "apps/base/data/articles.json"
INTERCOM_ROOT = "https://intercom.help/gyana/en/articles"

register = template.Library()


@functools.cache
def get_articles():
    return json.load(open(ARTICLES_PATH, "r"))


@register.inclusion_tag("components/link_article.html")
def link_article(collection: str, name: str):
    # will error if does not exist (deliberate)
    return {"article_url": f"{INTERCOM_ROOT}/{get_articles()[collection][name]}"}
