from allauth.account.models import EmailAddress
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from hijack.contrib.admin import HijackUserAdminMixin

from apps.teams.admin import TeamMembershipInline

from .models import ApprovedWaitlistEmail, ApprovedWaitlistEmailBatch, CustomUser


class EmailAddressInline(admin.TabularInline):
    model = EmailAddress
    list_display = ("email", "user", "primary", "verified")
    list_filter = ("primary", "verified")


@admin.register(CustomUser)
class CustomUserAdmin(HijackUserAdminMixin, UserAdmin):
    list_display = UserAdmin.list_display
    list_per_page = 20
    change_form_template = "users/admin/change_form.html"
    readonly_fields = [
        "username",
        "first_name",
        "last_name",
        "email",
        "last_login",
        "date_joined",
    ]
    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Password", {"fields": ("first_name", "last_name")}),
        ("Permissions", {"fields": ("is_active", "is_staff", "is_superuser")}),
        ("Important dates", {"fields": ("last_login", "date_joined")}),
    )
    list_display = ("email", "first_name", "last_name", "is_staff")
    search_fields = ("email", "first_name", "last_name")
    inlines = [TeamMembershipInline, EmailAddressInline]

    def change_view(self, request, object_id, form_url="", extra_context=None):
        extra_context = {
            "hijack_button": self.hijack_button(
                request, CustomUser.objects.get(pk=object_id)
            )
        }
        return super().change_view(request, object_id, form_url, extra_context)

    def has_add_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


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
