from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import TemplateView
from rest_framework.decorators import api_view

from apps.teams.models import Team

from .content import get_content


class Home(TemplateView):
    template_name = "web/home.html"

    def get(self, request, *args, **kwargs):

        if request.user.is_authenticated:
            if not request.user.onboarded:
                return redirect("users:onboarding")

            if request.user.teams.count():
                session_team_id = request.session.get("team_id")
                team_id = (
                    session_team_id
                    if session_team_id
                    and Team.objects.filter(pk=session_team_id).exists()
                    else request.user.teams.first().id
                )

                return redirect("teams:detail", team_id)

            return HttpResponseRedirect(reverse("teams:create"))

        if not settings.ENABLE_WEBSITE:
            return redirect("account_login")

        return super().get(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["content"] = get_content("home.yaml")
        return context


class Pricing(TemplateView):
    template_name = "web/pricing.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["content"] = get_content("pricing.yaml")
        return context


class About(TemplateView):
    template_name = "web/about.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["content"] = get_content("about.yaml")
        return context


class PrivacyPolicy(TemplateView):
    template_name = "web/privacy_policy.html"


class TermsOfUse(TemplateView):
    template_name = "web/terms_of_use.html"


@api_view(["POST"])
def toggle_sidebar(request):
    request.session["sidebar_collapsed"] = not request.session.get(
        "sidebar_collapsed", True
    )

    return HttpResponse(200)
