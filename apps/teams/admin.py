from django.contrib import admin

from apps.invites.admin import InviteInline

from .models import Membership, Team


class MembershipInline(admin.TabularInline):
    model = Membership
    list_display = ["user", "role"]


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "row_limit"]
    fields = ["id", "name", "row_limit", "row_count", "row_count_calculated"]
    readonly_fields = ["id", "row_count", "row_count_calculated"]
    inlines = [MembershipInline, InviteInline]
