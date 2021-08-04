import uuid

from apps.utils.frames import TurboFrameUpdateView
from django.urls.base import reverse

from .models import Dashboard


class DashboardShare(TurboFrameUpdateView):
    template_name = "dashboards/share.html"
    model = Dashboard
    fields = []
    turbo_frame_dom_id = "dashboard-share"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["dont_hide_body"] = True
        return context

    def form_valid(self, form):
        r = super().form_valid(form)
        if self.object.shared_status == Dashboard.SharedStatus.PRIVATE:
            self.object.shared_status = Dashboard.SharedStatus.PUBLIC
            self.object.shared_id = self.object.shared_id or uuid.uuid4()
        else:
            self.object.shared_status = Dashboard.SharedStatus.PRIVATE
        self.object.save()
        return r

    def get_success_url(self) -> str:
        return reverse(
            "dashboards:share",
            args=(self.object.id,),
        )
