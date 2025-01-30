import functools
import json

from django import template

DOCS_JSON = "apps/base/data/docs.json"
LOOM_JSON = "apps/base/data/loom.json"

DOCS_ROOT = "https://gyana.github.io/docs"
LOOM_ROOT = "https://www.loom.com"

register = template.Library()


@functools.cache
def get_docs():
    return json.load(open(DOCS_JSON, "r"))


@functools.cache
def get_loom():
    return json.load(open(LOOM_JSON, "r"))


def get_loom_embed_url(loom_id):
    return f"{LOOM_ROOT}/embed/{loom_id}?hideOwner=true"


@register.inclusion_tag("components/link_article.html")
def link_article(collection: str, name: str):
    print(get_docs())
    # will error if does not exist (deliberate)
    return {"article_url": f"{DOCS_ROOT}/{get_docs()[collection][name]}"}


@register.inclusion_tag("components/link_video.html")
def link_video(name: str):
    # will error if does not exist (deliberate)
    return {"article_url": f"{LOOM_ROOT}/share/{get_loom()[name]}"}


@register.inclusion_tag("components/embed_loom.html")
def embed_loom(video: str):
    # will error if does not exist (deliberate)
    return {"loom_url": get_loom_embed_url(get_loom()[video])}


@register.simple_tag
def article_url(collection: str, name: str):
    if (collection_obj := get_docs().get(collection)) and (
        article := collection_obj.get(name)
    ):
        return f"{DOCS_ROOT}/{article}"
    return DOCS_ROOT
