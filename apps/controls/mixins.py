from turbo_response import TurboStream

from apps.dashboards.mixins import DashboardMixin
from apps.widgets.frames import add_output_context


class UpdateWidgetsMixin(DashboardMixin):
    def get_widget_stream_responses(self, control):
        streams = []
        for widget in self.page.widgets.all():
            if widget.date_column and widget.is_valid:
                context = {
                    "widget": widget,
                    "dashboard": self.dashboard,
                    "project": self.project,
                    "page": self.page,
                }
                add_output_context(
                    context,
                    widget,
                    self.request,
                    control,
                )
                streams.append(
                    TurboStream(f"widgets-output-{widget.id}-stream")
                    .replace.template("widgets/output.html", context)
                    .render(request=self.request)
                )
        return streams
