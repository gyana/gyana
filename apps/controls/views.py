from django.db import transaction
from django.urls.base import reverse
from turbo_response import TurboStream
from turbo_response.response import TurboStreamResponse
from turbo_response.views import TurboStreamDeleteView

from apps.base.views import TurboCreateView
from apps.controls.models import Control, ControlWidget

from .mixins import UpdateWidgetsMixin


class ControlWidgetCreate(UpdateWidgetsMixin, TurboCreateView):
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
                *self.get_widget_stream_responses(form.instance.control),
                TurboStream("dashboard-widget-placeholder").remove.render(),
                TurboStream("dashboard-widget-container")
                .append.template(
                    "controls/control-widget.html",
                    {
                        "object": form.instance,
                        "control": form.instance.control,
                        "project": self.dashboard.project,
                        "dashboard": self.dashboard,
                        "page": self.page,
                    },
                )
                .render(request=self.request),
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


class ControlWidgetDelete(UpdateWidgetsMixin, TurboStreamDeleteView):
    template_name = "controls/delete.html"
    model = ControlWidget

    def delete(self, request, *args, **kwargs):
        self.object_id = self.get_object().id
        if self.page.control_widgets.count() != 1:
            return super().delete(request, *args, **kwargs)

        self.page.control.delete()

        return TurboStreamResponse(
            [
                *self.get_widget_stream_responses(None),
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
