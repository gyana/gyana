import functools
import json

from django import template

INTERCOM_JSON = "apps/base/data/intercom.json"
LOOM_JSON = "apps/base/data/loom.json"

INTERCOM_ROOT = "https://intercom.help/gyana/en/articles"
LOOM_ROOT = "https://www.loom.com/embed"

register = template.Library()


@functools.cache
def get_interom():
    return json.load(open(INTERCOM_JSON, "r"))


@functools.cache
def get_loom():
    return json.load(open(LOOM_JSON, "r"))


@register.inclusion_tag("components/link_article.html")
def link_article(collection: str, name: str):
    # will error if does not exist (deliberate)
    return {"article_url": f"{INTERCOM_ROOT}/{get_interom()[collection][name]}"}


@register.inclusion_tag("components/link_video.html")
def link_video(name: str):
    # will error if does not exist (deliberate)
    return {"article_url": f"{INTERCOM_ROOT}/{get_interom()['videos'][name]}"}


@register.inclusion_tag("components/embed_loom.html")
def embed_loom(video: str):
    # will error if does not exist (deliberate)
    return {"loom_url": f"{LOOM_ROOT}/{get_loom()[video]}?hideOwner=true"}


@register.simple_tag
def article_url(collection: str, name: str):
    if (collection_obj := get_interom().get(collection)) and (
        article := collection_obj.get(name)
    ):
        return f"{INTERCOM_ROOT}/{article}"
    return INTERCOM_ROOT
