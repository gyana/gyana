import logging

import analytics
from apps.dashboards.mixins import DashboardMixin
from apps.tables.models import Table
from apps.utils.formset_update_view import FormsetUpdateView
from apps.utils.segment_analytics import WIDGET_CONFIGURED_EVENT, WIDGET_CREATED_EVENT
from apps.widgets.serializers import WidgetSerializer
from apps.widgets.visuals import chart_to_output, table_to_output
from django.db import transaction
from django.db.models.query import QuerySet
from django.urls import reverse
from django.views.decorators.http import condition
from django.views.generic import DetailView, ListView
from django.views.generic.edit import UpdateView
from rest_framework import mixins, viewsets
from turbo_response import TurboStream
from turbo_response.response import TurboStreamResponse
from turbo_response.views import TurboCreateView, TurboStreamDeleteView

from .forms import FilterFormset, WidgetConfigForm, WidgetDuplicateForm
from .models import WIDGET_CHOICES_ARRAY, Widget


class WidgetList(DashboardMixin, ListView):
    template_name = "widgets/list.html"
    model = Widget
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["choices"] = WIDGET_CHOICES_ARRAY

        return context_data

    def get_queryset(self) -> QuerySet:
        return Widget.objects.filter(dashboard=self.dashboard)


class WidgetCreate(DashboardMixin, TurboCreateView):
    template_name = "widgets/create.html"
    model = Widget
    fields = ["kind"]

    def form_valid(self, form):
        form.instance.dashboard = self.dashboard

        # give different dimensions to text widget
        # TODO: make an abstraction with default values per widget kind
        if form.instance.kind == Widget.Kind.TEXT:
            form.instance.width = 30
            form.instance.height = 200

        with transaction.atomic():
            super().form_valid(form)
            self.dashboard.save()

        analytics.track(
            self.request.user.id,
            WIDGET_CREATED_EVENT,
            {
                "id": form.instance.id,
                "dashboard_id": self.dashboard.id,
            },
        )

        return TurboStreamResponse(
            [
                TurboStream("dashboard-widget-placeholder").remove.render(),
                TurboStream("dashboard-widget-container")
                .append.template(
                    "widgets/widget_component.html",
                    {
                        "object": form.instance,
                        "project": self.dashboard.project,
                        "dashboard": self.dashboard,
                        "is_new": True,
                    },
                )
                .render(request=self.request),
            ]
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
            attrs={"description": "Copy of " + (self.object.description or "")}
        )
        clone.save()
        self.clone = clone
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse(
            "dashboard_widgets:update",
            args=(self.project.id, self.dashboard.id, self.clone.id),
        )


class WidgetUpdate(DashboardMixin, FormsetUpdateView):
    template_name = "widgets/update.html"
    model = Widget
    form_class = WidgetConfigForm

    @property
    def formsets(self):
        return [FilterFormset]

    def get_formset_kwargs(self, formset):
        table = self.request.POST.get("table") or getattr(self.object, "table")
        if table:
            return {
                "schema": Table.objects.get(
                    pk=table.pk if isinstance(table, Table) else table
                ).schema
            }

        return {}

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.get_object().dashboard.project
        return kwargs

    def get_success_url(self) -> str:
        if self.request.POST.get("submit") == "Save & Preview":
            return reverse(
                "dashboard_widgets:update",
                args=(
                    self.project.id,
                    self.dashboard.id,
                    self.object.id,
                ),
            )
        return reverse(
            "project_dashboards:detail",
            args=(self.project.id, self.dashboard.id),
        )

    def form_valid(self, form):
        r = super().form_valid(form)

        analytics.track(
            self.request.user.id,
            WIDGET_CONFIGURED_EVENT,
            {
                "id": form.instance.id,
                "dashboard_id": self.dashboard.id,
                "type": form.instance.kind,
            },
        )

        return r


class WidgetDelete(TurboStreamDeleteView):
    template_name = "widgets/delete.html"
    model = Widget

    def get_turbo_stream_target(self):
        return f"widget-{self.object.pk}"

    def get_success_url(self) -> str:
        return reverse(
            "project_dashboards:detail",
            args=(self.project.id, self.dashboard.id),
        )


class WidgetPartialUpdate(viewsets.GenericViewSet, mixins.UpdateModelMixin):
    serializer_class = WidgetSerializer
    queryset = Widget.objects.all()


# Turbo frames


def last_modified_widget_output(request, pk):
    widget = Widget.objects.get(pk=pk)
    return (
        max(widget.updated, widget.table.data_updated)
        if widget.table
        else widget.updated
    )


def etag_widget_output(request, pk):
    last_modified = last_modified_widget_output(request, pk)
    return f"{int(last_modified.timestamp() * 1_000_000)}"


widget_output_condition = condition(
    etag_func=etag_widget_output, last_modified_func=last_modified_widget_output
)


class WidgetOutput(DetailView):
    template_name = "widgets/output.html"
    model = Widget

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        try:

            if self.object.is_valid:
                if self.object.kind == Widget.Kind.TABLE:
                    context_data.update(table_to_output(self.object))
                elif self.object.kind == Widget.Kind.TEXT:
                    pass
                else:
                    context_data.update(chart_to_output(self.object))
        except Exception as e:
            context_data["is_error"] = True
            logging.warning(e, exc_info=e)

        return context_data
