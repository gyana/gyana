import uuid

import analytics
from apps.base.analytics import DASHBOARD_SHARED_PUBLIC_EVENT
from apps.base.frames import TurboFrameDetailView, TurboFrameUpdateView
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

        if self.object.shared_status == Dashboard.SharedStatus.PUBLIC:
            analytics.track(
                self.request.user.id,
                DASHBOARD_SHARED_PUBLIC_EVENT,
                {"id": self.object.id},
            )
        return r

    def get_success_url(self) -> str:
        return reverse(
            "dashboards:share",
            args=(self.object.id,),
        )


class DashboardPreview(TurboFrameDetailView):
    template_name = "dashboards/preview.html"
    model = Dashboard
    turbo_frame_dom_id = "dashboard:preview"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.object.project
        return context
