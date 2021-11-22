from django.urls import reverse
from django.utils.functional import cached_property
from django.views.generic.edit import DeleteView
from turbo_response import TurboStream
from turbo_response.response import TurboStreamResponse

from apps.base.frames import TurboFrameCreateView, TurboFrameUpdateView
from apps.widgets.frames import add_output_context

from .forms import DateSlicerForm
from .models import DateSlicer


class DateSlicerCreate(TurboFrameCreateView):
    template_name = "dateslicers/create.html"
    model = DateSlicer
    form_class = DateSlicerForm
    turbo_frame_dom_id = "dateslicers:create"

    @cached_property
    def dashboard(self):
        from apps.dashboards.models import Dashboard

        return Dashboard.objects.get(pk=self.request.POST["dashboard_id"])

    def form_valid(self, form):
        r = super().form_valid(form)
        self.dashboard.date_slicer = form.instance
        self.dashboard.save()
        context = self.get_context_data()
        context["dashboard"] = self.dashboard
        context_update = {
            "object": self.object,
            "form": DateSlicerForm(instance=self.object),
        }

        return TurboStreamResponse(
            [
                TurboStream("dateslicers:create-stream")
                .replace.template(self.template_name, context)
                .render(request=self.request),
                TurboStream("dateslicers:update-stream")
                .replace.template("dateslicers/update.html", context_update)
                .render(request=self.request),
            ]
        )

    def get_success_url(self) -> str:
        return reverse("dateslicers:create")


class DateSlicerUpdate(TurboFrameUpdateView):
    template_name = "dateslicers/update.html"
    model = DateSlicer
    form_class = DateSlicerForm
    turbo_frame_dom_id = "dateslicers:update"

    def form_valid(self, form):
        super().form_valid(form)
        dashboard = form.instance.dashboard
        streams = []
        for widget in dashboard.widget_set.all():
            if widget.dateslice_column and widget.is_valid:
                context = {
                    "widget": widget,
                    "dashboard": dashboard,
                    "project": dashboard.project,
                }
                add_output_context(context, widget, self.request)
                streams.append(
                    TurboStream(f"widgets-output-{widget.id}-stream")
                    .replace.template("widgets/output.html", context)
                    .render(request=self.request)
                )
        return TurboStreamResponse(streams)

    def get_success_url(self) -> str:
        return reverse("dateslicers:update", args=(self.object.id,))


class DateSlicerDelete(DeleteView):
    template_name = "dateslicers/delete.html"
    model = DateSlicer

    def delete(self, request, *args, **kwargs):
        dashboard = self.get_object().dashboard
        super().delete(request, *args, **kwargs)
        dashboard.date_slicer = None
        return TurboStreamResponse(
            [
                TurboStream("dateslicers:update-stream").replace.render(
                    "<div id='dateslicers:update-stream'></div>", is_safe=True
                ),
                TurboStream("dateslicers:create-stream")
                .replace.template("dateslicers/create.html", {"dashboard": dashboard})
                .render(request=request),
            ]
        )

    def get_success_url(self) -> str:
        # Won't actually return a response to hear
        return reverse("dateslicers:create")
