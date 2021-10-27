from django.contrib import admin
from safedelete.admin import SafeDeleteAdmin, highlight_deleted

from apps.appsumo.admin import (
    AppsumoCodeInline,
    AppsumoExtraInline,
    AppsumoReviewInline,
)
from apps.invites.admin import InviteInline

from .models import Membership, Team


class UserMembershipInline(admin.TabularInline):
    model = Membership
    list_display = ["user", "role"]


class TeamMembershipInline(admin.TabularInline):
    model = Membership
    list_display = ["team", "role"]


@admin.register(Team)
class TeamAdmin(SafeDeleteAdmin):
    # Use `highlight_deleted` in place of name
    list_display = ("id", highlight_deleted, "row_limit") + SafeDeleteAdmin.list_display
    readonly_fields = ["id", "row_limit", "row_count", "row_count_calculated"]
    fields = readonly_fields + ["name", "override_row_limit"]

    inlines = [
        UserMembershipInline,
        AppsumoCodeInline,
        AppsumoReviewInline,
        AppsumoExtraInline,
        InviteInline,
    ]

    def row_limit(self, instance):
        return instance.row_limit
