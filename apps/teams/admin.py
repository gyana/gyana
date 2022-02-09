from django.contrib import admin
from safedelete.admin import SafeDeleteAdmin, highlight_deleted
from waffle.admin import FlagAdmin as WaffleFlagAdmin

from apps.appsumo.admin import (
    AppsumoCodeInline,
    AppsumoExtraInline,
    AppsumoReviewInline,
)
from apps.invites.admin import InviteInline

from .models import Flag, Membership, Team


class UserMembershipInline(admin.TabularInline):
    model = Membership
    list_display = ["user", "role"]


class TeamMembershipInline(admin.TabularInline):
    model = Membership
    list_display = ["team", "role"]


@admin.register(Team)
class TeamAdmin(SafeDeleteAdmin):
    # Use `highlight_deleted` in place of name
    list_display = (
        "id",
        highlight_deleted,
        "list_of_members",
        "plan_name",
        "plan_rows",
        "usage",
        "percent",
    )
    search_fields = ("name", "members__email")

    readonly_fields = ["id", "row_limit", "row_count", "row_count_calculated"]
    fields = readonly_fields + ["name", "override_row_limit"]
    list_per_page = 20

    def plan_name(self, obj):
        return obj.plan["name"]

    def list_of_members(self, obj):
        return ", ".join([str(p) for p in obj.members.all()])

    def usage(self, obj):
        return "{:,}".format(obj.row_count)

    def percent(self, obj):
        return "{:.1%}".format(obj.row_count / obj.row_limit)

    def plan_rows(self, obj):
        return "{:,}".format(obj.row_limit)

    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.prefetch_related("members")

    inlines = [
        UserMembershipInline,
        AppsumoCodeInline,
        AppsumoReviewInline,
        AppsumoExtraInline,
        InviteInline,
    ]

    def row_limit(self, instance):
        return instance.row_limit


class FlagAdmin(WaffleFlagAdmin):
    raw_id_fields = tuple(list(WaffleFlagAdmin.raw_id_fields) + ["teams"])


admin.site.register(Flag, FlagAdmin)
