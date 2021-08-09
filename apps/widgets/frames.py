import logging

import analytics
from apps.base.frames import (
    TurboFrameDetailView,
    TurboFrameFormsetUpdateView,
    TurboFrameListView,
)
from apps.base.segment_analytics import WIDGET_CONFIGURED_EVENT
from apps.dashboards.mixins import DashboardMixin
from apps.tables.models import Table
from apps.widgets.visuals import chart_to_output, table_to_output
from django.db.models.query import QuerySet
from django.urls import reverse
from django.views.decorators.http import condition
from django_tables2.config import RequestConfig
from django_tables2.tables import Table as DjangoTable
from django_tables2.views import SingleTableMixin
from turbo_response import TurboStream

from .forms import FORMS
from .models import WIDGET_CHOICES_ARRAY, Widget


def add_output_context(context, widget, request):
    if widget.is_valid:
        if widget.kind == Widget.Kind.TEXT:
            pass
        if widget.kind == Widget.Kind.TABLE:
            table = table_to_output(widget)
            context["table"] = RequestConfig(
                request,
            ).configure(table)
        else:
            chart, chart_id = chart_to_output(widget)
            context.update(chart)
            context["chart_id"] = chart_id


class WidgetList(DashboardMixin, TurboFrameListView):
    template_name = "widgets/list.html"
    model = Widget
    paginate_by = 20
    turbo_frame_dom_id = "widgets"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["choices"] = WIDGET_CHOICES_ARRAY

        return context_data

    def get_queryset(self) -> QuerySet:
        return Widget.objects.filter(dashboard=self.dashboard)


class WidgetUpdate(DashboardMixin, TurboFrameFormsetUpdateView):
    template_name = "widgets/update.html"
    model = Widget
    turbo_frame_dom_id = "widget-modal"

    def get_form_class(self):
        return FORMS[self.request.POST.get("kind") or self.object.kind]

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
        if self.request.POST.get("submit") == "Save & Preview":
            return r

        context = {
            "widget": self.object,
            "project": self.project,
            "dashboard": self.dashboard,
        }
        add_output_context(context, self.object, self.request)
        return (
            TurboStream(f"widgets-output-{self.object.id}-stream")
            .replace.template("widgets/output.html", context)
            .response(request=self.request)
        )

    def form_invalid(self, form):
        r = super().form_invalid(form)
        if self.request.POST.get("close"):
            context = {
                "widget": self.object,
                "project": self.project,
                "dashboard": self.dashboard,
            }
            add_output_context(context, self.object, self.request)
            return (
                TurboStream(f"widgets-output-{self.object.id}-stream")
                .replace.template("widgets/output.html", context)
                .response(request=self.request)
            )
        return r


class WidgetOutput(DashboardMixin, SingleTableMixin, TurboFrameDetailView):
    template_name = "widgets/output.html"
    model = Widget
    paginate_by = 15

    def get_turbo_frame_dom_id(self):
        return f"widgets-output-{self.object.id}"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.get_object().dashboard.project
        try:
            add_output_context(context, self.object, self.request)

        except Exception as e:
            context["is_error"] = True
            logging.warning(e, exc_info=e)

        return context

    def get_table(self, **kwargs):
        if self.object.is_valid and self.object.kind == Widget.Kind.TABLE:
            table = table_to_output(self.object)
            return RequestConfig(
                self.request, paginate=self.get_table_pagination(table)
            ).configure(table)
        return type("DynamicTable", (DjangoTable,), {})(data=[])


# ====== Not used right now =======
# TODO: decide whether we want to cache the output of the chart or
# Remove this. You will also need to add back the caching logic in urls.py.
# We removed this for now because with the modal we are rendering the same FusionChart
# Twice which leads to an id conflict


def last_modified_widget_output(request, pk):
    widget = Widget.objects.get(pk=pk)
    return (
        max(widget.updated, widget.table.data_updated)
        if widget.table
        else widget.updated
    )


def etag_widget_output(request, pk):
    last_modified = last_modified_widget_output(request, pk)
    return str(int(last_modified.timestamp() * 1_000_000))


widget_output_condition = condition(
    etag_func=etag_widget_output, last_modified_func=last_modified_widget_output
)

# ==================================================
