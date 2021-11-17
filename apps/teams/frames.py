from apps.base.frames import TurboFrameTemplateView

class TeamListModal(TurboFrameTemplateView):
    template_name = "teams/list.html"
    turbo_frame_dom_id = "teams:list"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        return context