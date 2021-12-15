from apps.base.turbo import TurboCreateView
from apps.controls.models import Control, ControlWidget
from apps.dashboards.mixins import DashboardMixin


class ControlWidgetCreate(DashboardMixin, TurboCreateView):
    template_name = "controls/create-control-widget.html"
    model = ControlWidget
    fields = ["x", "y", "page"]

    def form_valid(self, form):
        if not self.page.has_control:
            form.instance.control = Control(page=self.page)
        else:
            form.instance.control = self.page.control

        return super().form_valid(form)
