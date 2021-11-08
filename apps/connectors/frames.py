from apps.base.frames import TurboFrameDetailView

from .models import Connector


class ConnectorIcon(TurboFrameDetailView):
    template_name = "columns/status.html"
    model = Connector
    fields = []
    turbo_frame_dom_id = "connectors:icon"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        self.object.sync_updates_from_fivetran()

        context_data["icon"] = self.object.integration.state_icon
        context_data["text"] = self.object.integration.state_text

        return context_data


class ConnectorStatus(TurboFrameDetailView):
    template_name = "connectors/status.html"
    model = Connector
    fields = []
    turbo_frame_dom_id = "connectors:status"

    def get_context_data(self, **kwargs):
        self.object.sync_updates_from_fivetran()
        return super().get_context_data(**kwargs)
