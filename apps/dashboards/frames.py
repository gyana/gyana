from django.db.models import Count, Q
from django.shortcuts import redirect
from django.urls.base import reverse
from django_tables2 import SingleTableMixin, SingleTableView
from turbo_response import TurboStream
from turbo_response.response import TurboStreamResponse

from apps.base.frames import (
    TurboFrameDetailView,
    TurboFrameTemplateView,
    TurboFrameUpdateView,
)
from apps.dashboards.forms import DashboardShareForm
from apps.dashboards.tables import DashboardHistoryTable, DashboardUpdateTable
from apps.projects.mixins import ProjectMixin
from apps.widgets.models import Widget

from .forms import DashboardForm, DashboardVersionSaveForm
from .models import Dashboard, DashboardVersion


class DashboardOverview(ProjectMixin, TurboFrameTemplateView):
    template_name = "dashboards/overview.html"
    turbo_frame_dom_id = "dashboards:overview"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        integrations = self.project.integration_set
        widgets = Widget.objects.filter(page__dashboard__project=self.project)
        # equivalent to is_valid, but efficient query
        incomplete = widgets.annotate(agg_count=Count("aggregations")).exclude(
            (Q(kind=Widget.Kind.TEXT) & ~Q(text_content=None))
            | (Q(kind=Widget.Kind.IMAGE) & ~Q(image=None))
            | (Q(kind=Widget.Kind.IFRAME) & ~Q(url=None))
            | (Q(kind=Widget.Kind.TABLE) & ~Q(table=None))
            | (Q(kind__in=[Widget.Kind.METRIC, Widget.Kind.GAUGE]) & Q(agg_count=1))
            | (Q(kind=Widget.Kind.RADAR) & Q(agg_count__gte=3))
            | (Q(kind=Widget.Kind.FUNNEL) & Q(agg_count__gte=2))
            | (~Q(table=None) & ~Q(dimension=None) & ~Q(aggregations__column=None))
        )
        dashboards_incomplete = (
            incomplete.values_list("page__dashboard").distinct().count()
        )

        context_data["dashboards"] = {
            "all": self.project.dashboard_set.order_by("-updated").all()[:5],
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
            position=self.request.GET.get("dashboardPage", 1)
        )
        return context


class DashboardSettings(ProjectMixin, TurboFrameUpdateView):
    template_name = "dashboards/settings.html"
    model = Dashboard
    form_class = DashboardForm
    turbo_frame_dom_id = "dashboard:settings"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["category"] = self.request.GET.get("category")

        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Dashboard.Category.choices

        return context

    def form_invalid(self, form):
        context = self.get_context_data()
        return TurboStreamResponse(
            [
                TurboStream(self.turbo_frame_dom_id)
                .replace.template(self.template_name, context)
                .render()
            ]
        )

    def get_success_url(self) -> str:
        return reverse(
            "project_dashboards:detail", args=(self.project.id, self.object.id)
        )


class DashboardHistory(ProjectMixin, SingleTableMixin, TurboFrameUpdateView):
    template_name = "dashboards/history.html"
    model = Dashboard
    table_class = DashboardHistoryTable
    paginate_by = 20
    turbo_frame_dom_id = "dashboard:history"
    form_class = DashboardVersionSaveForm

    def get_table_data(self):
        if self.request.GET.get("tab") == "history":
            return self.object.updates
        return self.object.versions

    def get_table_class(self):
        if self.request.GET.get("tab") == "history":
            return DashboardUpdateTable
        return super().get_table_class()

    def get_success_url(self) -> str:
        return reverse(
            "project_dashboards:history", args=(self.project.id, self.object.id)
        )


class DashboardVersionRename(TurboFrameUpdateView):
    model = DashboardVersion
    fields = ("name",)
    template_name = "dashboards/version_name.html"

    def get_turbo_frame_dom_id(self):
        return f"version-name-{self.object.id}"

    def get_success_url(self) -> str:
        return reverse("dashboards:version-rename", args=(self.object.id,))
