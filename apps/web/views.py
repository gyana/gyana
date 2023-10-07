from django.http import HttpResponse
from django.views.generic import TemplateView
from rest_framework.decorators import api_view

from .cache import cache_site
from .config import FUNCTIONS, NODE_CONFIG, WIDGET_KIND_TO_WEB
from .content import get_content


class Home(TemplateView):
    template_name = "web/home.html"

    def get(self, request, *args, **kwargs):
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
