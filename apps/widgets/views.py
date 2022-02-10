import analytics
from django.urls import reverse
from turbo_response import TurboStream
from turbo_response.response import TurboStreamResponse
from turbo_response.views import TurboStreamDeleteView

from apps.base.analytics import WIDGET_CREATED_EVENT, WIDGET_DUPLICATED_EVENT
from apps.base.views import TurboCreateView, TurboUpdateView
from apps.dashboards.mixins import DashboardMixin

from .forms import WidgetDuplicateForm
from .models import Widget


class WidgetCreate(DashboardMixin, TurboCreateView):
    template_name = "widgets/create.html"
    model = Widget
    fields = ["kind", "x", "y", "page"]

    def form_valid(self, form):

        # give different dimensions to text widget
        # TODO: make an abstraction with default values per widget kind
        if form.instance.kind == Widget.Kind.TEXT:
            form.instance.width = 300
            form.instance.height = 195

        super().form_valid(form)

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
        lowest_widget = self.page.widgets.order_by("-y").first()
        clone = self.object.make_clone(
            attrs={
                "name": "Copy of " + (self.object.name or ""),
                "y": lowest_widget.y + lowest_widget.height,
            }
        )

        clone.save()
        self.clone = clone

        super().form_valid(form)

        analytics.track(
            self.request.user.id,
            WIDGET_DUPLICATED_EVENT,
            {
                "id": form.instance.id,
                "dashboard_id": self.dashboard.id,
            },
        )
        self.request.GET.mode = "edit"
        return TurboStreamResponse(
            [
                TurboStream("dashboard-widget-placeholder").remove.render(),
                TurboStream("dashboard-widget-container")
                .append.template(
                    "widgets/widget_component.html",
                    {
                        "object": clone,
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
            args=(self.project.id, self.dashboard.id, self.clone.id),
        )


class WidgetDelete(DashboardMixin, TurboStreamDeleteView):
    template_name = "widgets/delete.html"
    model = Widget

    def get_turbo_stream_target(self):
        return f"widget-{self.object.pk}"

    def get_success_url(self) -> str:
        return reverse(
            "project_dashboards:detail",
            args=(self.project.id, self.dashboard.id),
        )
