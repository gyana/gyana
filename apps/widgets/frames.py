import logging
from decimal import Decimal

import analytics
from django.urls import reverse
from django.views.generic import DetailView, UpdateView
from django_tables2.tables import Table as DjangoTable
from django_tables2.views import SingleTableMixin
from honeybadger import honeybadger
from turbo_response import TurboStream
from turbo_response.response import TurboStreamResponse

from apps.base.analytics import (
    WIDGET_COMPLETED_EVENT,
    WIDGET_CONFIGURED_EVENT,
    WIDGET_PREVIEWED_EVENT,
)
from apps.base.core.table_data import RequestConfig, get_table
from apps.base.core.utils import error_name_to_snake
from apps.base.templates import template_exists
from apps.base.views import LiveUpdateView
from apps.columns.currency_symbols import CURRENCY_SYMBOLS_MAP
from apps.controls.bigquery import DATETIME_FILTERS
from apps.dashboards.mixins import DashboardMixin
from apps.tables.bigquery import get_query_from_table
from apps.tables.models import Table
from apps.widgets.visuals import chart_to_output, metric_to_output, table_to_output

from .forms import FORMS, STYLE_FORMS, DefaultStyleForm, WidgetSourceForm
from .models import Widget


def add_output_context(context, widget, request, control, url=None):
    if not widget.is_valid:
        return
    if widget.kind == Widget.Kind.TEXT:
        pass
    elif widget.kind == Widget.Kind.IFRAME:
        pass
    elif widget.kind == Widget.Kind.IMAGE:
        pass
    elif widget.kind == Widget.Kind.TABLE:
        # avoid duplicating work for widget output
        if "table" not in context:
            table = table_to_output(widget, control, url)
            context["table"] = RequestConfig(
                request, paginate={"per_page": widget.table_paginate_by}
            ).configure(table)
    elif widget.kind == Widget.Kind.METRIC:
        metric = metric_to_output(widget, control)
        if (
            metric
            and widget.compare_previous_period
            and (used_control := widget.control if widget.has_control else control)
        ):
            if DATETIME_FILTERS.get(used_control.date_range) and (
                previous_metric := metric_to_output(widget, control, True)
            ):
                context["change"] = (metric - previous_metric) / previous_metric * 100
                context["period"] = DATETIME_FILTERS[used_control.date_range][
                    "previous_label"
                ]
            else:
                context["zero_division"] = True
        column = widget.aggregations.first()
        context["column"] = column
        if column.currency:
            context["currency"] = CURRENCY_SYMBOLS_MAP[column.currency]
        context["metric"] = (
            round(metric, column.rounding)
            if isinstance(metric, (float, Decimal))
            else metric
        )
    else:
        chart, chart_id = chart_to_output(widget, control)
        context.update(chart)
        context["chart_id"] = chart_id


class WidgetName(UpdateView):
    model = Widget
    fields = ("name",)
    template_name = "widgets/name.html"

    def get_success_url(self) -> str:
        return reverse(
            "widgets:name",
            args=(self.object.id,),
        )


class WidgetUpdate(DashboardMixin, LiveUpdateView):
    model = Widget

    def get_turbo_stream_response(self, context):
        return TurboStreamResponse(
            [
                TurboStream(f"widgets-output-{self.object.id}")
                .update.template("widgets/output.html", context)
                .render(request=self.request),
                TurboStream(f"widget-name-{self.object.id}")
                .replace.template("widgets/_widget_title.html", {"object": self.object})
                .render(),
            ]
        )

    @property
    def tab(self):
        return self.request.GET.get("tab", "data" if self.object.table else "source")

    def get_output_context(self):
        context = {
            "widget": self.object,
            "project": self.project,
            "dashboard": self.dashboard,
        }
        try:
            add_output_context(
                context,
                self.object,
                self.request,
                self.object.page.control if self.object.page.has_control else None,
                url=self.get_success_url()
                if self.is_preview_request
                else reverse(
                    "dashboard_widgets:output",
                    args=(
                        self.project.id,
                        self.dashboard.id,
                        self.object.id,
                    ),
                ),
            )
            if self.object.error:
                self.object.error = None
        except Exception as e:
            error = error_name_to_snake(e)
            self.object.error = error
            if not template_exists(f"widgets/errors/{error}.html"):
                logging.warning(e, exc_info=e)
                honeybadger.notify(e)

        return context

    def get_template_names(self):
        if self.object.kind == Widget.Kind.IFRAME:
            return "widgets/update-simple.html"
        if self.object.kind == Widget.Kind.IMAGE:
            return "widgets/update-simple.html"

        return "widgets/update.html"

    def get_form_class(self):
        if self.tab == "style":
            return STYLE_FORMS.get(self.object.kind, DefaultStyleForm)

        if self.tab == "source" and self.object.kind not in [
            Widget.Kind.IFRAME,
            Widget.Kind.IMAGE,
        ]:
            return WidgetSourceForm

        return FORMS[self.request.POST.get("kind", self.object.kind)]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        if self.tab == "style":
            return kwargs
        if self.tab == "source":
            kwargs["project"] = self.dashboard.project
            return kwargs
        table = self.request.POST.get("table") or getattr(self.object, "table")
        if table is not None:
            kwargs["schema"] = (
                table if isinstance(table, Table) else Table.objects.get(pk=table)
            ).schema

        return kwargs

    def get_success_url(self) -> str:
        if self.is_preview_request:
            base_url = reverse(
                "dashboard_widgets:update",
                args=(
                    self.project.id,
                    self.dashboard.id,
                    self.object.id,
                ),
            )
            return f"{base_url}?tab={self.tab if self.tab!='source' else 'data'}"

        return reverse(
            "project_dashboards:detail",
            args=(self.project.id, self.dashboard.id),
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["tab"] = self.tab

        if self.tab == "data" and self.object.kind not in [
            Widget.Kind.TEXT,
            Widget.Kind.IFRAME,
            Widget.Kind.IMAGE,
        ]:
            context["show_date_column"] = bool(
                context["form"].get_live_field("date_column")
            )

        return context

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
        context = self.get_output_context()

        if self.is_preview_request:
            analytics.track(
                self.request.user.id,
                WIDGET_PREVIEWED_EVENT,
                {
                    "id": form.instance.id,
                    "dashboard_id": self.dashboard.id,
                    "type": form.instance.kind,
                },
            )
            return r

        analytics.track(
            self.request.user.id,
            WIDGET_COMPLETED_EVENT,
            {
                "id": form.instance.id,
                "dashboard_id": self.dashboard.id,
                "type": form.instance.kind,
            },
        )

        return self.get_turbo_stream_response(context)

    def form_invalid(self, form):
        r = super().form_invalid(form)
        if self.request.POST.get("close"):
            # This is called when the x/close button is clicked
            context = self.get_output_context()

            return self.get_turbo_stream_response(context)
        return r


class WidgetOutput(DashboardMixin, SingleTableMixin, DetailView):
    template_name = "widgets/output.html"
    model = Widget
    paginate_by = 15

    def get_context_data(self, **kwargs):
        context = None
        try:
            context = super().get_context_data(**kwargs)

            add_output_context(
                context,
                self.object,
                self.request,
                self.object.page.control if self.object.page.has_control else None,
            )
        except Exception as e:
            if context is None:
                context = {
                    "dashboard": self.dashboard,
                    "page": self.object.page,
                    "project": self.dashboard.project,
                    "object": self.object,
                    "widget": self.object,
                }
            error_template = f"widgets/errors/{error_name_to_snake(e)}.html"
            if template_exists(error_template):
                context["error_template"] = error_template
            else:
                context["error_template"] = "widgets/errors/default.html"

        return context

    def get_table(self, **kwargs):
        if self.object.is_valid and self.object.kind == Widget.Kind.TABLE:
            self.paginate_by = self.object.table_paginate_by
            table = table_to_output(
                self.object,
                self.object.page.control if self.object.page.has_control else None,
            )
            return RequestConfig(
                self.request,
                paginate={
                    **self.get_table_pagination(table),
                    "per_page": self.object.table_paginate_by,
                },
            ).configure(table)
        return type("DynamicTable", (DjangoTable,), {})(data=[])


class WidgetInput(DashboardMixin, SingleTableMixin, DetailView):
    template_name = "widgets/input.html"
    model = Widget
    paginate_by = 15

    def get_table(self, **kwargs):
        if self.object.table:
            query = get_query_from_table(self.object.table)
            table = get_table(query.schema(), query)
            return RequestConfig(
                self.request, paginate=self.get_table_pagination(table)
            ).configure(table)
        return type("DynamicTable", (DjangoTable,), {})(data=[])
