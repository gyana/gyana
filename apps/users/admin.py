from allauth.account.models import EmailAddress
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from apps.teams.admin import TeamMembershipInline

from .models import ApprovedWaitlistEmail, ApprovedWaitlistEmailBatch, CustomUser


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


@admin.register(ApprovedWaitlistEmail)
class ApprovedWaitlistEmailAdmin(admin.ModelAdmin):
    list_display = ["email"]
    fields = ["email"]
    readonly_fields = ["email"]


@admin.register(ApprovedWaitlistEmailBatch)
class ApprovedWaitlistEmailBatchAdmin(admin.ModelAdmin):
    list_display = ["data", "success"]
    fields = ["data", "success"]
    readonly_fields = ["success"]
