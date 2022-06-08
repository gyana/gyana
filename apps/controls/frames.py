from django.urls import reverse
from django.utils.functional import cached_property
from turbo_response import TurboStream
from turbo_response.response import HttpResponseSeeOther, TurboStreamResponse

from apps.base.frames import TurboFrameUpdateView

from .forms import ControlForm
from .mixins import UpdateWidgetsMixin
from .models import Control


class ControlUpdate(UpdateWidgetsMixin, TurboFrameUpdateView):
    template_name = "controls/update.html"
    model = Control
    form_class = ControlForm
    turbo_frame_dom_id = "controls:update-widget"

    def get_stream_response(self, form):
        streams = self.get_widget_stream_responses(form.instance, form.instance.page)
        current_context = self.get_context_data()
        is_public = current_context.get("is_public", False)
        template = "controls/control_public.html" if is_public else "controls/control-widget.html"

        for control_widget in form.instance.page.control_widgets.iterator():
            context = {
                "object": control_widget,
                "control": form.instance,
                "dashboard": self.dashboard,
                "project": self.project,
                "is_public": is_public,
                "request": self.request,
            }
            streams.append(
                TurboStream(f"control-widget-{control_widget.id}")
                .replace.template(template, context)
                .render(request=self.request)
            )

        return TurboStreamResponse(streams)

    def form_valid(self, form):
        r = super().form_valid(form)
        if form.is_live:
            return r
        return self.get_stream_response(form)

    def get_success_url(self) -> str:
        return reverse(
            "dashboard_controls:update-widget",
            args=(
                self.project.id,
                self.dashboard.id,
                self.object.id,
            ),
        )


class ControlPublicUpdate(ControlUpdate):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_public"] = True
        return context

    def get_success_url(self) -> str:
        return reverse(
            "dashboard_controls:update-public",
            args=(
                self.project.id,
                self.dashboard.id,
                self.object.id,
            ),
        )

    def form_valid(self, form):
        if form.is_live:
            return HttpResponseSeeOther(self.get_success_url())
        return self.get_stream_response(form)

    @cached_property
    def page(self):
        return self.dashboard.pages.get(
            position=self.request.GET.get("dashboardPage", 1)
        )
