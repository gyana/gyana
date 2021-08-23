from allauth.account.models import EmailAddress
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from apps.teams.admin import TeamMembershipInline

from .models import CustomUser


class EmailAddressInline(admin.TabularInline):
    model = EmailAddress
    list_display = ("email", "user", "primary", "verified")
    list_filter = ("primary", "verified")


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    list_display = UserAdmin.list_display

    fieldsets = UserAdmin.fieldsets + (
        (
            "Custom Fields",
            {"fields": ("avatar",)},
        ),
    )

    inlines = [TeamMembershipInline, EmailAddressInline]
