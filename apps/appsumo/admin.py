from django.contrib import admin

from .models import AppsumoCode, RedeemedCodes, RefundedCodes

admin.site.register(RedeemedCodes)
admin.site.register(RefundedCodes)


@admin.register(AppsumoCode)
class AppsumoCodeAdmin(admin.ModelAdmin):
    list_display = ("code", "team", "redeemed")
    fields = ["code", "team", "redeemed", "redeemed_by"]
    readonly_fields = ["code", "redeemed", "redeemed_by"]


class AppsumoCodeInline(admin.TabularInline):
    model = AppsumoCode
    fields = ["code", "redeemed", "redeemed_by"]
    readonly_fields = ["code", "redeemed", "redeemed_by"]

    def has_add_permission(self, request, obj):
        return False

    def has_delete_permission(self, request, obj):
        return False
