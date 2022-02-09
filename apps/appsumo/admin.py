from django.contrib import admin

from .models import (
    AppsumoCode,
    AppsumoExtra,
    AppsumoReview,
    PurchasedCodes,
    RefundedCodes,
    UploadedCodes,
)


@admin.register(RefundedCodes)
class RefundedCodesAdmin(admin.ModelAdmin):
    list_display = ["data", "downloaded", "success"]
    fields = ["data", "downloaded", "success"]
    readonly_fields = ["success"]


@admin.register(PurchasedCodes)
class PurchasedCodesAdmin(admin.ModelAdmin):
    list_display = ["data", "deal", "success"]
    fields = ["data", "deal", "success"]
    readonly_fields = ["success"]


@admin.register(UploadedCodes)
class UploadedCodesAdmin(admin.ModelAdmin):
    list_display = ["data", "success"]
    fields = ["data", "success"]
    readonly_fields = ["success"]


@admin.register(AppsumoCode)
class AppsumoCodeAdmin(admin.ModelAdmin):
    list_display = ["code", "team", "redeemed"]
    readonly_fields = ["code", "redeemed", "redeemed_by"]
    fields = readonly_fields + ["team"]


class AppsumoCodeInline(admin.TabularInline):
    model = AppsumoCode
    readonly_fields = fields = ["code", "redeemed", "redeemed_by"]

    def has_add_permission(self, request, obj):
        return False

    def has_delete_permission(self, request, obj):
        return False


class AppsumoReviewInline(admin.StackedInline):
    model = AppsumoReview
    fields = ["review_link"]


class AppsumoExtraInline(admin.StackedInline):
    model = AppsumoExtra
    fields = ["rows", "reason"]
