from django.db import transaction
from django.urls.base import reverse
from turbo_response import TurboStream
from turbo_response.response import TurboStreamResponse

from apps.base.turbo import TurboCreateView
from apps.controls.forms import ControlForm
from apps.controls.models import Control, ControlWidget
from apps.dashboards.mixins import DashboardMixin


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
                        "control": form.instance.control,
                        "project": self.dashboard.project,
                        "dashboard": self.dashboard,
                        "page": self.page,
                        "form": ControlForm(instance=self.object.control),
                    },
                )
                .render(request=self.request),
            ]
        )

    # TODO: not right yet
    def get_success_url(self) -> str:
        return reverse(
            "controls:update",
            args=(
                self.project.id,
                self.dashboard.id,
                self.object.id,
            ),
        )
