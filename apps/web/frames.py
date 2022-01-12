from apps.base.frames import TurboFrameTemplateView


class HelpModal(TurboFrameTemplateView):
    template_name = "web/help.html"
    turbo_frame_dom_id = "web:help"


class ChangelogModal(TurboFrameTemplateView):
    template_name = "web/changelog.html"
    turbo_frame_dom_id = "web:changelog"
