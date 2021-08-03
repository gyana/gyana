import analytics
from apps.dashboards.mixins import DashboardMixin
from apps.utils.segment_analytics import WIDGET_CREATED_EVENT
from django.db import transaction
from django.urls import reverse
from turbo_response import TurboStream
from turbo_response.response import TurboStreamResponse
from turbo_response.views import TurboCreateView, TurboStreamDeleteView, TurboUpdateView

from .forms import WidgetDuplicateForm
from .models import Widget


class WidgetCreate(DashboardMixin, TurboCreateView):
    template_name = "widgets/create.html"
    model = Widget
    fields = ["kind"]

    def form_valid(self, form):
        form.instance.dashboard = self.dashboard

        # give different dimensions to text widget
        # TODO: make an abstraction with default values per widget kind
        if form.instance.kind == Widget.Kind.TEXT:
            form.instance.width = 300
            form.instance.height = 200

        if lowest_widget := self.dashboard.widget_set.order_by("-y").first():
            form.instance.y = lowest_widget.y + lowest_widget.height

        with transaction.atomic():
            super().form_valid(form)
            self.dashboard.save()

        analytics.track(
            self.request.user.id,
            WIDGET_CREATED_EVENT,
            {
                "id": form.instance.id,
                "dashboard_id": self.dashboard.id,
            },
        )

        return TurboStreamResponse(
            [
                TurboStream("dashboard-widget-placeholder").remove.render(),
                TurboStream("dashboard-widget-container")
                .append.template(
                    "widgets/widget_component.html",
                    {
                        "object": form.instance,
                        "project": self.dashboard.project,
                        "dashboard": self.dashboard,
                        "is_new": True,
                    },
                )
                .render(request=self.request),
            ]
        )

    def get_success_url(self) -> str:
        return reverse(
            "dashboard_widgets:update",
            args=(
                self.project.id,
                self.dashboard.id,
                self.object.id,
            ),
        )


class WidgetDetail(DashboardMixin, TurboUpdateView):
    template_name = "widgets/detail.html"
    model = Widget
    form_class = WidgetDuplicateForm

    def form_valid(self, form):
        clone = self.object.make_clone(
            attrs={"description": "Copy of " + (self.object.description or "")}
        )
        clone.save()
        self.clone = clone
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse(
            "dashboard_widgets:update",
            args=(self.project.id, self.dashboard.id, self.clone.id),
        )


class WidgetDelete(TurboStreamDeleteView):
    template_name = "widgets/delete.html"
    model = Widget

    def get_turbo_stream_target(self):
        return f"widget-{self.object.pk}"

    def get_success_url(self) -> str:
        return reverse(
            "project_dashboards:detail",
            args=(self.project.id, self.dashboard.id),
        )
