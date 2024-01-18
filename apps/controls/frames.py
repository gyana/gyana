from django.shortcuts import render
from django.urls import reverse
from django.utils.functional import cached_property
from django_htmx.http import retarget, trigger_client_event

from apps.base.views import UpdateView
from apps.dashboards.mixins import DashboardMixin

from .forms import ControlForm
from .models import Control


class ControlUpdate(DashboardMixin, UpdateView):
    template_name = "controls/update.html"
    model = Control
    form_class = ControlForm

    def get_stream_response(self, form):
        context = self.get_context_data()
        is_public = context.get("is_public", False)
        template = (
            "controls/control_public.html"
            if is_public
            else "controls/control-widget.html"
        )

        # todo: fix for multiple control widgets
        control_widget = form.instance.page.control_widgets.first()

        res = render(
            self.request,
            template,
            {
                "object": control_widget,
                "control": form.instance,
                "dashboard": self.dashboard,
                "project": self.project,
                "is_public": is_public,
                "request": self.request,
            },
        )

        return retarget(
            trigger_client_event(
                trigger_client_event(res, "gy-control", {}), "closeModal", {}
            ),
            f"#control-widget-{control_widget.id}",
        )

    def form_valid(self, form):
        r = super().form_valid(form)
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
        return self.get_stream_response(form)

    @cached_property
    def page(self):
        return self.dashboard.pages.get(
            position=self.request.GET.get("dashboardPage", 1)
        )
