from django.db import transaction
from django.urls.base import reverse
from django.views.generic.edit import DeleteView
from turbo_response import TurboStream
from turbo_response.response import TurboStreamResponse
from turbo_response.views import TurboStreamDeleteView

from apps.base.turbo import TurboCreateView
from apps.controls.forms import ControlForm
from apps.controls.models import Control, ControlWidget
from apps.dashboards.mixins import DashboardMixin
from apps.widgets.frames import add_output_context


class ControlWidgetCreate(DashboardMixin, TurboCreateView):
    template_name = "controls/create.html"
    model = ControlWidget
    fields = ["x", "y", "page"]

    def form_valid(self, form):
        if not self.page.has_control:
            form.instance.control = Control(page=self.page)

        else:
            form.instance.control = self.page.control

        with transaction.atomic():
            form.instance.control.save()
            super().form_valid(form)

        return TurboStreamResponse(
            [
                TurboStream("dashboard-widget-placeholder").remove.render(),
                TurboStream("dashboard-widget-container")
                .append.template(
                    "controls/control-widget.html",
                    {
                        "object": form.instance,
                        "project": self.dashboard.project,
                        "dashboard": self.dashboard,
                        "page": self.page,
                    },
                )
                .render(request=self.request),
            ]
        )

    # TODO: not right yet
    def get_success_url(self) -> str:
        return reverse(
            "project_dashboards:detail",
            args=(
                self.project.id,
                self.dashboard.id,
            ),
        )


class ControlWidgetDelete(DashboardMixin, TurboStreamDeleteView):
    template_name = "controls/delete.html"
    model = ControlWidget

    def delete(self, request, *args, **kwargs):
        if self.page.control_widgets.count() != 1:
            return super().delete(request, *args, **kwargs)

        self.object_id = self.get_object().id
        self.page.control.delete()
        streams = []
        for widget in self.page.widgets.all():
            context = {
                "widget": widget,
                "dashboard": self.dashboard,
                "page": self.page,
                "project": self.project,
            }
            add_output_context(context, widget, self.request, None)
            streams.append(
                TurboStream(f"widgets-output-{widget.id}-stream")
                .replace.template("widgets/output.html", context)
                .render(request=self.request)
            )
        return TurboStreamResponse(
            [
                *streams,
                TurboStream(f"control-widget-{self.object_id}").remove.render(),
            ]
        )

    def get_success_url(self) -> str:
        return reverse(
            "project_dashboards:detail",
            args=(
                self.project.id,
                self.dashboard.id,
            ),
        )

    def get_turbo_stream_target(self):
        return f"control-widget-{self.object_id}"
