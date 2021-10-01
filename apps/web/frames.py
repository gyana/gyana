from apps.base.frames import TurboFrameTemplateView


class HelpModal(TurboFrameTemplateView):
    template_name = "web/help.html"
    turbo_frame_dom_id = "web:help"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        return context_data

