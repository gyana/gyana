from django.contrib import admin

from .models import (
    AppsumoCode,
    AppsumoReview,
    PurchasedCodes,
    RefundedCodes,
    UploadedCodes,
)


class BaseFileCodesAdmin(admin.ModelAdmin):
    list_display = ["data", "downloaded", "success"]
    fields = ["data", "downloaded", "success"]
    readonly_fields = ["success"]


@admin.register(RefundedCodes)
class AppsumoCodeAdmin(BaseFileCodesAdmin):
    pass


@admin.register(PurchasedCodes)
class AppsumoCodeAdmin(BaseFileCodesAdmin):
    pass


@admin.register(UploadedCodes)
class AppsumoCodeAdmin(BaseFileCodesAdmin):
    pass


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

    def has_add_permission(self, request, obj):
        return False

    def has_delete_permission(self, request, obj):
        return False
