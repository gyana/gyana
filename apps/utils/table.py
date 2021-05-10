import django_tables2 as tables
from django.contrib.humanize.templatetags.humanize import naturaltime


class NaturalDatetimeColumn(tables.Column):
    def render(self, value):
        return naturaltime(value)
