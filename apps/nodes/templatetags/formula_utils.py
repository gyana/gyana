from django import template

from apps.base.templatetags.help_utils import DOCS_ROOT

register = template.Library()


@register.simple_tag
def link_function(intercom_id):
    return f"{DOCS_ROOT}/functions/#{intercom_id}"
