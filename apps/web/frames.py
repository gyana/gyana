import random

from apps.base.frames import TurboFrameTemplateView
from apps.nodes.config import NODE_CONFIG
from apps.web.content import get_content
from apps.widgets.models import WIDGET_KIND_TO_WEB


def get_services_obj():
    return get_content("services.yaml")


def get_services_grouped(group_n):
    services = list(get_services_obj().values())
    random.shuffle(services)
    length = len(services)
    n = int(length / group_n)
    services_grouped = [
        {"services": services[i : i + n], "animation": random.randint(15, 35)}
        for i in range(0, group_n * n, n)
    ]
    return services_grouped


class HelpModal(TurboFrameTemplateView):
    template_name = "web/help.html"
    turbo_frame_dom_id = "web:help"


class ChangelogModal(TurboFrameTemplateView):
    template_name = "web/changelog.html"
    turbo_frame_dom_id = "web:changelog"


class IntegrationsDemo(TurboFrameTemplateView):
    template_name = "web/demo/integrations.html"
    turbo_frame_dom_id = "web:integrations-demo"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["services_grouped"] = get_services_grouped(6)
        return context


class WorkflowsDemo(TurboFrameTemplateView):
    template_name = "web/demo/workflows.html"
    turbo_frame_dom_id = "web:workflows-demo"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        node_config = {
            k: v for k, v in NODE_CONFIG.items() if k not in ["input", "output", "text"]
        }
        context["node_config"] = node_config
        return context


class DashboardsDemo(TurboFrameTemplateView):
    template_name = "web/demo/dashboards.html"
    turbo_frame_dom_id = "web:dashboards-demo"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["widget_config"] = WIDGET_KIND_TO_WEB
        return context


class SupportDemo(TurboFrameTemplateView):
    template_name = "web/site/home/support.html"
    turbo_frame_dom_id = "web:support-demo"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["content"] = get_content("home.yaml")
        return context


class SearchIntegrationsDemo(TurboFrameTemplateView):
    template_name = "web/demo/search_integrations.html"
    turbo_frame_dom_id = "web:search-integrations-demo"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["content"] = get_content("integrations.yaml")
        return context
