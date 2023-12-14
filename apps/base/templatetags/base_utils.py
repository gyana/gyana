import json

from django.template.defaulttags import register


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def form_name(item):
    return item.split("-")[-1]
