from django.conf import settings
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import redirect
from django.urls import reverse
from django.views.generic import TemplateView
from rest_framework.decorators import api_view

from apps.columns.transformer import FUNCTIONS
from apps.connectors.fivetran.config import get_services_obj
from apps.nodes.config import NODE_CONFIG
from apps.teams.models import Team
from apps.web.frames import get_services_grouped
from apps.widgets.models import WIDGET_KIND_TO_WEB

from .cache import cache_site
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

        return cache_site(super().get)(request, *args, **kwargs)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["content"] = get_content("home.yaml")
        node_config = {
            k: v for k, v in NODE_CONFIG.items() if k not in ["input", "output", "text"]
        }
        context["workflow_statistics"] = {
            "node_count": len(node_config.keys()),
            "function_count": len(FUNCTIONS),
        }
        context["widget_count"] = len(WIDGET_KIND_TO_WEB.keys())
        return context


class Pricing(TemplateView):
    template_name = "web/pricing.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["content"] = get_content("pricing.yaml")
        return context


class Integrations(TemplateView):
    template_name = "web/integrations.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["services"] = get_services_obj()
        context["services_grouped"] = get_services_grouped(4)
        context["content"] = get_content("integrations.yaml")
        return context


class Integration(TemplateView):
    template_name = "web/integration.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["service"] = get_services_obj()[kwargs["id"]]
        context["content"] = get_content("integration.yaml", context)
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


class BookADemo(TemplateView):
    template_name = "web/book_a_demo.html"


@api_view(["POST"])
def toggle_sidebar(request):
    request.session["sidebar_collapsed"] = not request.session.get(
        "sidebar_collapsed", True
    )

    return HttpResponse(200)


class ECommerce(TemplateView):
    template_name = "web/use_case/ecommerce.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["services"] = get_services_obj()
        context["services_grouped"] = get_services_grouped(4)
        context["content"] = {
            **get_content("use_case/ecommerce.yaml"),
            **get_content("integrations.yaml"),
        }
        return context
