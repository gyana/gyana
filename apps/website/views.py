from django.conf import settings
from django.shortcuts import redirect
from django.views.generic import TemplateView


class Landing(TemplateView):
    template_name = "website/landing.html"

    def get(self, request, *args, **kwargs):

        if request.user.is_authenticated:
            return redirect("web:home")

        if not settings.ENABLE_WEBSITE:
            return redirect("account_login")

        return super().get(request, *args, **kwargs)
