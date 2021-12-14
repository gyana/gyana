from django.urls import reverse
from django.utils.functional import cached_property
from django.views.generic.edit import DeleteView
from turbo_response import TurboStream
from turbo_response.response import HttpResponseSeeOther, TurboStreamResponse

from apps.base.frames import TurboFrameCreateView, TurboFrameUpdateView
from apps.dashboards.mixins import DashboardMixin
from apps.widgets.frames import add_output_context

from .forms import ControlForm
from .models import Control


class ControlCreate(DashboardMixin, TurboFrameCreateView):
    template_name = "controls/create.html"
    model = Control
    fields = []
    turbo_frame_dom_id = "controls:create"

    def form_valid(self, form):
        form.instance.page = self.page
        super().form_valid(form)
        context = self.get_context_data()
        context_update = {
            "object": self.object,
            "dashboard": self.dashboard,
            "project": self.project,
            "page": self.page,
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
        base_url = reverse(
            "controls:create",
            args=(
                self.project.id,
                self.dashboard.id,
            ),
        )
        return f"{base_url}?page={self.page.position}"


class ControlUpdate(DashboardMixin, TurboFrameUpdateView):
    template_name = "controls/update.html"
    model = Control
    form_class = ControlForm
    turbo_frame_dom_id = "controls:update"

    def get_stream_response(self, form):
        streams = []
        for widget in self.dashboard.get_all_widgets():
            if widget.date_column and widget.is_valid:
                context = {
                    "widget": widget,
                    "dashboard": self.dashboard,
                    "project": self.project,
                    "page": self.page,
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
                .replace.template(self.template_name, self.get_context_data(form=form))
                .render(request=self.request),
            ]
        )

    def form_valid(self, form):
        r = super().form_valid(form)
        if form.is_live:
            return r
        return self.get_stream_response(form)

    def get_success_url(self) -> str:
        return reverse(
            "controls:update",
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
            "controls:update-public",
            args=(
                self.project.id,
                self.dashboard.id,
                self.object.id,
            ),
        )

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.request.method == "GET":
            kwargs.update({"data": self.request.GET})
        return kwargs

    def get(self, request, *args, **kwargs):
        if not self.request.GET:
            return super().get(request, *args, **kwargs)
        self.request.POST = self.request.GET
        return self.post(request, *args, **kwargs)

    def form_valid(self, form):
        if form.is_live:
            return HttpResponseSeeOther(self.get_success_url())
        return self.get_stream_response(form)

    @cached_property
    def page(self):
        return self.dashboard.pages.get(position=self.request.GET.get("page", 1))


class ControlDelete(DashboardMixin, DeleteView):
    template_name = "controls/delete.html"
    model = Control

    def delete(self, request, *args, **kwargs):
        super().delete(request, *args, **kwargs)
        return TurboStreamResponse(
            [
                TurboStream("controls:update-stream").replace.render(
                    "<div id='controls:update-stream'></div>", is_safe=True
                ),
                TurboStream("controls:create-stream")
                .replace.template(
                    "controls/create.html",
                    {
                        "dashboard": self.dashboard,
                        "project": self.project,
                        "page": self.page,
                    },
                )
                .render(request=request),
            ]
        )

    def get_success_url(self) -> str:
        # Won't actually return a response to here
        return reverse(
            "controls:create",
            args=(
                self.project.id,
                self.dashboard.id,
            ),
        )
