from django.contrib import admin

from .models import Invite


class InviteInline(admin.TabularInline):
    model = Invite
    fields = ["email", "role"]
    readonly_fields = ["email"]

    def has_add_permission(self, request, obj):
        return False
