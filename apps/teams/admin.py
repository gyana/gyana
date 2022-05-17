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
    readonly_fields = ["user"]
    list_display = ["user", "role"]


class TeamMembershipInline(admin.TabularInline):
    model = Membership
    readonly_fields = ["team"]
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

    readonly_fields = [
        highlight_deleted,
        "plan_rows",
        "usage",
        "percent",
        "row_count_calculated",
        "plan_credits",
    ]
    fieldsets = (
        (None, {"fields": readonly_fields}),
        (
            "Manual override",
            {
                "fields": [
                    "override_row_limit",
                    "override_credit_limit",
                    "override_rows_per_integration_limit",
                    "has_free_trial",
                ]
            },
        ),
    )
    list_per_page = 20

    def list_of_members(self, obj):
        return ", ".join([str(p) for p in obj.members.all()])

    def plan_name(self, obj):
        return obj.plan["name"]

    def plan_rows(self, obj):
        return "{:,}".format(obj.row_limit)

    def plan_credits(self, obj):
        return "{:,}".format(obj.credits)

    def usage(self, obj):
        return "{:,}".format(obj.row_count)

    def percent(self, obj):
        return "{:.1%}".format(obj.row_count / obj.row_limit)

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

    def has_add_permission(self, request, obj=None):
        return False


class FlagAdmin(WaffleFlagAdmin):
    raw_id_fields = tuple(list(WaffleFlagAdmin.raw_id_fields) + ["teams"])


admin.site.register(Flag, FlagAdmin)
