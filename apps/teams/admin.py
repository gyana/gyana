from django.contrib import admin

from .models import Membership, Team


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ["user", "team", "role"]
    list_filter = ["team"]


class MembershipInlineAdmin(admin.TabularInline):
    model = Membership
    list_display = ["user", "role"]


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ["name"]
    inlines = (MembershipInlineAdmin,)
