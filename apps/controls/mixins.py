from turbo_response import TurboStream

from apps.dashboards.mixins import DashboardMixin
from apps.widgets.frames import add_output_context


class UpdateWidgetsMixin(DashboardMixin):
    def get_widget_stream_responses(self, control, page):
        streams = []
        for widget in page.widgets.all():
            if not (widget.has_control) and widget.date_column and widget.is_valid:
                context = {
                    "widget": widget,
                    "dashboard": self.dashboard,
                    "project": self.project,
                    "page": page,
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
