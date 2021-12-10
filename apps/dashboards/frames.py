from django.db.models import Count, Q
from django.urls.base import reverse
from turbo_response import TurboStream
from turbo_response.response import TurboStreamResponse

from apps.base.frames import (
    TurboFrameDetailView,
    TurboFrameTemplateView,
    TurboFrameUpdateView,
)
from apps.dashboards.forms import DashboardShareForm
from apps.projects.mixins import ProjectMixin
from apps.widgets.models import Widget

from .forms import DashboardForm
from .models import Dashboard


class DashboardOverview(ProjectMixin, TurboFrameTemplateView):
    template_name = "dashboards/overview.html"
    turbo_frame_dom_id = "dashboards:overview"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        integrations = self.project.integration_set
        widgets = Widget.objects.filter(dashboard__project=self.project)
        # equivalent to is_valid, but efficient query
        incomplete = widgets.annotate(agg_count=Count("aggregations")).exclude(
            Q(kind=Widget.Kind.TEXT)
            | (Q(kind=Widget.Kind.TABLE) & ~Q(table=None))
            | (Q(kind=Widget.Kind.RADAR) & ~Q(agg_count__lte=3))
            | (~Q(table=None) & ~Q(dimension=None) & ~Q(aggregations__column=None))
        )
        dashboards_incomplete = incomplete.values_list("dashboard").distinct().count()

        context_data["dashboards"] = {
            "total": self.project.dashboard_set.count(),
            "widgets": widgets.count(),
            "incomplete": dashboards_incomplete,
            "operational": dashboards_incomplete == 0,
        }

        context_data["integrations"] = {"ready": integrations.ready().count()}

        return context_data


class DashboardShare(TurboFrameUpdateView):
    template_name = "dashboards/share.html"
    form_class = DashboardShareForm
    model = Dashboard
    turbo_frame_dom_id = "dashboard-share"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["dont_hide_body"] = True
        return context

    def get_success_url(self) -> str:
        return reverse(
            "dashboards:share",
            args=(self.object.id,),
        )


class DashboardPreview(TurboFrameDetailView):
    template_name = "dashboards/preview.html"
    model = Dashboard
    turbo_frame_dom_id = "dashboard:preview"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.object.project
        context["page"] = self.object.pages.get(
            position=self.request.GET.get("page", 1)
        )
        return context


class DashboardSettings(ProjectMixin, TurboFrameUpdateView):
    template_name = "dashboards/settings.html"
    model = Dashboard
    form_class = DashboardForm
    turbo_frame_dom_id = "dashboard:settings"

    def get_success_url(self) -> str:
        return reverse(
            "project_dashboards:detail", args=(self.project.id, self.object.id)
        )

    def form_invalid(self, form):
        context = self.get_context_data()
        return TurboStreamResponse(
            [
                TurboStream(self.turbo_frame_dom_id)
                .replace.template(self.template_name, context)
                .render()
            ]
        )
