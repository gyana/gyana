from django import template
from django.urls import reverse
from django.urls.exceptions import NoReverseMatch

register = template.Library()


def _get_admin_url(instance):
    if not instance:
        raise NoReverseMatch()
    return reverse(f"admin:{instance._meta.db_table}_change", args=(instance.id,))


@register.filter()
def admin_url(instance):
    try:
        return _get_admin_url(instance)
    except NoReverseMatch:
        return reverse("admin:index")


@register.filter
def admin_url_found(instance):
    try:
        _get_admin_url(instance)
        return True
    except NoReverseMatch:
        return False


@register.filter
def verbose_name(instance):
    return instance._meta.verbose_name
