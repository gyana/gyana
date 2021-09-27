import uuid

import analytics
from apps.base.analytics import DASHBOARD_SHARED_PUBLIC_EVENT
from apps.base.frames import (
    TurboFrameDetailView,
    TurboFrameTemplateView,
    TurboFrameUpdateView,
)
from apps.projects.mixins import ProjectMixin
from apps.widgets.models import Widget
from django.db.models import Count, Q
from django.urls.base import reverse

from .models import Dashboard


class DashboardOverview(ProjectMixin, TurboFrameTemplateView):
    template_name = "dashboards/overview.html"
    turbo_frame_dom_id = "dashboards:overview"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

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

        return context_data


class DashboardShare(TurboFrameUpdateView):
    template_name = "dashboards/share.html"
    model = Dashboard
    fields = []
    turbo_frame_dom_id = "dashboard-share"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["dont_hide_body"] = True
        return context

    def form_valid(self, form):
        r = super().form_valid(form)
        if self.object.shared_status == Dashboard.SharedStatus.PRIVATE:
            self.object.shared_status = Dashboard.SharedStatus.PUBLIC
            self.object.shared_id = self.object.shared_id or uuid.uuid4()
        else:
            self.object.shared_status = Dashboard.SharedStatus.PRIVATE
        self.object.save()

        if self.object.shared_status == Dashboard.SharedStatus.PUBLIC:
            analytics.track(
                self.request.user.id,
                DASHBOARD_SHARED_PUBLIC_EVENT,
                {"id": self.object.id},
            )
        return r

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
        return context
