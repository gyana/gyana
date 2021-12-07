from django.urls import reverse
from django.utils.functional import cached_property
from django.views.generic.edit import DeleteView
from turbo_response import TurboStream
from turbo_response.response import HttpResponseSeeOther, TurboStreamResponse

from apps.base.frames import TurboFrameCreateView, TurboFrameUpdateView
from apps.widgets.frames import add_output_context

from .forms import ControlForm
from .models import Control


class ControlCreate(TurboFrameCreateView):
    template_name = "controls/create.html"
    model = Control
    fields = []
    turbo_frame_dom_id = "controls:create"

    @cached_property
    def dashboard(self):
        from apps.dashboards.models import Dashboard

        return Dashboard.objects.get(pk=self.request.POST["dashboard_id"])

    def form_valid(self, form):
        form.instance.dashboard = self.dashboard
        super().form_valid(form)
        context = self.get_context_data()
        context["dashboard"] = self.dashboard
        context_update = {
            "object": self.object,
            "form": ControlForm(instance=self.object),
        }

        return TurboStreamResponse(
            [
                TurboStream("controls:create-stream")
                .replace.template(self.template_name, context)
                .render(request=self.request),
                TurboStream("controls:update-stream")
                .replace.template("controls/update.html", context_update)
                .render(request=self.request),
            ]
        )

    def get_success_url(self) -> str:
        return reverse("controls:create")


class ControlUpdate(TurboFrameUpdateView):
    template_name = "controls/update.html"
    model = Control
    form_class = ControlForm
    turbo_frame_dom_id = "controls:update"

    def get_stream_response(self, form):
        dashboard = form.instance.dashboard
        streams = []
        for widget in dashboard.widget_set.all():
            if widget.date_column and widget.is_valid:
                context = {
                    "widget": widget,
                    "dashboard": dashboard,
                    "project": dashboard.project,
                }
                add_output_context(context, widget, self.request, form.instance)
                streams.append(
                    TurboStream(f"widgets-output-{widget.id}-stream")
                    .replace.template("widgets/output.html", context)
                    .render(request=self.request)
                )
        return TurboStreamResponse(
            [
                *streams,
                TurboStream("controls:update-stream")
                .replace.template(self.template_name, self.get_context_data())
                .render(request=self.request),
            ]
        )

    def form_valid(self, form):
        r = super().form_valid(form)
        if form.is_live:
            return r
        return self.get_stream_response(form)

    def get_success_url(self) -> str:
        return reverse("controls:update", args=(self.object.id,))


class ControlPublicUpdate(ControlUpdate):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["is_public"] = True
        return context

    def get_success_url(self) -> str:
        return reverse("controls:update-public", args=(self.object.id,))

    def form_valid(self, form):
        if form.is_live:
            return HttpResponseSeeOther(self.get_success_url())
        return self.get_stream_response(form)


class ControlDelete(DeleteView):
    template_name = "controls/delete.html"
    model = Control

    def delete(self, request, *args, **kwargs):
        dashboard = self.get_object().dashboard
        super().delete(request, *args, **kwargs)
        return TurboStreamResponse(
            [
                TurboStream("controls:update-stream").replace.render(
                    "<div id='controls:update-stream'></div>", is_safe=True
                ),
                TurboStream("controls:create-stream")
                .replace.template("controls/create.html", {"dashboard": dashboard})
                .render(request=request),
            ]
        )

    def get_success_url(self) -> str:
        # Won't actually return a response to hear
        return reverse("controls:create")
