import analytics
from django.shortcuts import render
from django.urls import reverse
from django.views.generic import DeleteView

from apps.base.analytics import WIDGET_CREATED_EVENT, WIDGET_DUPLICATED_EVENT
from apps.base.views import CreateView, UpdateView
from apps.dashboards.mixins import DashboardMixin

from .forms import WidgetCreateForm, WidgetDuplicateForm
from .models import Widget


class WidgetCreate(DashboardMixin, CreateView):
    template_name = "widgets/create.html"
    model = Widget
    form_class = WidgetCreateForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["dashboard"] = self.dashboard
        return kwargs

    def form_valid(self, form):
        # give different dimensions to text widget
        # TODO: make an abstraction with default values per widget kind
        if form.instance.kind == Widget.Kind.TEXT:
            form.instance.width = 300
            form.instance.height = 195

        super().form_valid(form)

        analytics.track(
            self.request.user.id,
            WIDGET_CREATED_EVENT,
            {
                "id": form.instance.id,
                "dashboard_id": self.dashboard.id,
            },
        )

        return render(
            self.request,
            "widgets/widget_component.html",
            {
                "object": form.instance,
                "project": self.dashboard.project,
                "dashboard": self.dashboard,
                "is_new": True,
            },
        )

    def get_success_url(self) -> str:
        return reverse(
            "dashboard_widgets:update",
            args=(
                self.project.id,
                self.dashboard.id,
                self.object.id,
            ),
        )


class WidgetDetail(DashboardMixin, UpdateView):
    template_name = "widgets/detail.html"
    model = Widget
    form_class = WidgetDuplicateForm

    def form_valid(self, form):
        clone = self.object.make_clone(
            attrs={
                "name": "Copy of " + self.object.name if self.object.name else "",
                "y": self.object.y + self.object.height,
            }
        )

        clone.save()
        self.clone = clone

        super().form_valid(form)

        analytics.track(
            self.request.user.id,
            WIDGET_DUPLICATED_EVENT,
            {
                "id": form.instance.id,
                "dashboard_id": self.dashboard.id,
            },
        )
        self.request.GET.mode = "edit"

        return render(
            self.request,
            "widgets/widget_component.html",
            {
                "object": clone,
                "project": self.dashboard.project,
                "dashboard": self.dashboard,
                "is_new": True,
            },
        )

    def get_success_url(self) -> str:
        return reverse(
            "dashboard_widgets:update",
            args=(self.project.id, self.dashboard.id, self.clone.id),
        )


class WidgetDelete(DashboardMixin, DeleteView):
    template_name = "widgets/delete.html"
    model = Widget

    def get_success_url(self) -> str:
        return reverse(
            "project_dashboards:detail",
            args=(self.project.id, self.dashboard.id),
        )


class WidgetMovePage(DashboardMixin, UpdateView):
    model = Widget
    fields = ("page",)
    template_name = "widgets/forms/move_page.html"

    def get_success_url(self) -> str:
        return f"{reverse('project_dashboards:detail', args=(self.project.id,self.dashboard.id),)}?dashboardPage={self.object.page.position}"
