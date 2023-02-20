from django.template.defaulttags import register


@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)


@register.filter
def js_const(item):
    return item.replace("-", "_")


@register.filter
def form_name(item):
    return item.split("-")[-1]
