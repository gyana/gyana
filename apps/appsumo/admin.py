from django.contrib import admin

from .models import AppsumoCode, PurchasedCodes, RefundedCodes, UploadedCodes


@admin.register(RefundedCodes)
class AppsumoCodeAdmin(admin.ModelAdmin):
    list_display = ["data", "downloaded", "success"]
    fields = ["data", "downloaded", "success"]
    readonly_fields = ["success"]


@admin.register(PurchasedCodes)
class AppsumoCodeAdmin(admin.ModelAdmin):
    list_display = ["data", "downloaded", "success"]
    fields = ["data", "downloaded", "success"]
    readonly_fields = ["success"]


@admin.register(UploadedCodes)
class AppsumoCodeAdmin(admin.ModelAdmin):
    list_display = ["data", "downloaded", "success"]
    fields = ["data", "downloaded", "success"]
    readonly_fields = ["success"]


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
