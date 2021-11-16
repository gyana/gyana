from django import template

from apps.base.templatetags.help_utils import INTERCOM_ROOT

register = template.Library()


@register.simple_tag
def link_function(intercom_id):
    return f"{INTERCOM_ROOT}/5738138/#{intercom_id}"
