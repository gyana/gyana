from django.contrib import admin

from .models import Team, Membership, Invitation


@admin.register(Membership)
class MembershipAdmin(admin.ModelAdmin):
    list_display = ['user', 'team', 'role']
    list_filter = ['team']


@admin.register(Invitation)
class InvitationAdmin(admin.ModelAdmin):
    list_display = ['id', 'team', 'email', 'role', 'is_accepted']
    list_filter = ['team', 'is_accepted']


class MembershipInlineAdmin(admin.TabularInline):
    model = Membership
    list_display = ['user', 'role']


@admin.register(Team)
class TeamAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'subscription']
    inlines = (MembershipInlineAdmin, )
