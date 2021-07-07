import json

from django import template

register = template.Library()


@register.filter("read_json")
def read_json(path):
    with open(path, "r") as file:
        data = file.read()
    return json.loads(data)
