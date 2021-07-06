from django.contrib import admin

from .models import Invite

# @admin.register(Invite)
# class InviteAdmin(admin.ModelAdmin):
#     list_display = ["id", "team", "email", "role", "is_accepted"]
#     list_filter = ["team", "is_accepted"]
