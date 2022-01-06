from django.contrib import admin
from waffle.admin import FlagAdmin as WaffleFlagAdmin

from .models import Flag


class TeamFlagAdmin(WaffleFlagAdmin):
    raw_id_fields = tuple(list(WaffleFlagAdmin.raw_id_fields) + ["teams"])


admin.site.register(Flag, TeamFlagAdmin)
