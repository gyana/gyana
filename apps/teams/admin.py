from django.contrib import admin

from apps.invites.admin import InviteInline

from .models import Membership, Team


class UserMembershipInline(admin.TabularInline):
    model = Membership
    list_display = ["user", "role"]


class TeamMembershipInline(admin.TabularInline):
    model = Membership
    list_display = ["team", "role"]


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ["id", "name", "row_limit"]
    fields = ["id", "name", "row_limit", "row_count", "row_count_calculated"]
    readonly_fields = ["id", "row_count", "row_count_calculated"]
    inlines = [UserMembershipInline, InviteInline]
