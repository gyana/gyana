from django.db import transaction
from django.http import HttpResponseRedirect
from django.shortcuts import render
from django.urls.base import reverse
from django.views.generic import CreateView, DeleteView
from django_htmx.http import trigger_client_event

from apps.controls.models import Control, ControlWidget
from apps.dashboards.mixins import DashboardMixin


class ControlWidgetCreate(DashboardMixin, CreateView):
    template_name = "controls/create.html"
    model = ControlWidget
    fields = ["x", "y", "page"]

    def form_valid(self, form):
        if not form.instance.page.has_control:
            form.instance.control = Control(page=form.instance.page)

        else:
            form.instance.control = form.instance.page.control

        with transaction.atomic():
            form.instance.control.save()
            super().form_valid(form)

        res = render(
            self.request,
            "controls/control-widget.html",
            {
                "object": form.instance,
                "control": form.instance.control,
                "project": self.dashboard.project,
                "dashboard": self.dashboard,
                "page": form.instance.page,
            },
        )

        return trigger_client_event(res, "gy-control", {})

    def get_success_url(self) -> str:
        return reverse(
            "project_dashboards:detail",
            args=(
                self.project.id,
                self.dashboard.id,
            ),
        )


class ControlWidgetDelete(DashboardMixin, DeleteView):
    template_name = "controls/delete.html"
    model = ControlWidget

    def form_valid(self, form):
        success_url = self.get_success_url()

        if self.object.page.control_widgets.count() != 1:
            return super().delete(self, form)

        self.object.page.control.delete()
        return trigger_client_event(HttpResponseRedirect(success_url), "gy-control", {})

    def get_success_url(self) -> str:
        return reverse(
            "project_dashboards:detail",
            args=(
                self.project.id,
                self.dashboard.id,
            ),
        )
