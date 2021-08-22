from django import template

register = template.Library()


@register.filter
def db_table(instance):
    return instance._meta.db_table


@register.filter
def verbose_name(instance):
    return instance._meta.verbose_name
