import functools
import json

from django import template

INTERCOM_JSON = "apps/base/data/intercom.json"
LOOM_JSON = "apps/base/data/loom.json"

INTERCOM_ROOT = "https://support.gyana.com/en/articles"
LOOM_ROOT = "https://www.loom.com/embed"

register = template.Library()


@functools.cache
def get_intercom():
    return json.load(open(INTERCOM_JSON, "r"))


@functools.cache
def get_loom():
    return json.load(open(LOOM_JSON, "r"))


def get_loom_embed_url(loom_id):
    return f"{LOOM_ROOT}/{loom_id}?hideOwner=true"


@register.inclusion_tag("components/link_article.html")
def link_article(collection: str, name: str):
    # will error if does not exist (deliberate)
    return {"article_url": f"{INTERCOM_ROOT}/{get_intercom()[collection][name]}"}


@register.inclusion_tag("components/link_video.html")
def link_video(name: str):
    # will error if does not exist (deliberate)
    return {"article_url": f"{INTERCOM_ROOT}/{get_intercom()['videos'][name]}"}


@register.inclusion_tag("components/embed_loom.html")
def embed_loom(video: str):
    # will error if does not exist (deliberate)
    return {"loom_url": get_loom_embed_url(get_loom()[video])}


@register.simple_tag
def article_url(collection: str, name: str):
    if (collection_obj := get_intercom().get(collection)) and (
        article := collection_obj.get(name)
    ):
        return f"{INTERCOM_ROOT}/{article}"
    return INTERCOM_ROOT
