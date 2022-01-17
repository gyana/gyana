import logging

import analytics
from django.db.models.query import QuerySet
from django.urls import reverse
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
from apps.base.core.utils import error_name_to_snake
from apps.base.core.table_data import RequestConfig
from apps.base.frames import (
    TurboFrameDetailView,
    TurboFrameFormsetUpdateView,
    TurboFrameListView,
    TurboFrameUpdateView,
)
from apps.base.templates import template_exists
from apps.controls.bigquery import DATETIME_FILTERS
from apps.dashboards.mixins import DashboardMixin
from apps.tables.models import Table
from apps.widgets.visuals import chart_to_output, metric_to_output, table_to_output

from .forms import FORMS, WidgetStyleForm
from .models import Widget


def add_output_context(context, widget, request, control):
    if widget.is_valid:
        if widget.kind == Widget.Kind.TEXT:
            pass
        elif widget.kind == Widget.Kind.IFRAME:
            pass
        elif widget.kind == Widget.Kind.IMAGE:
            pass
        elif widget.kind == Widget.Kind.TABLE:
            # avoid duplicating work for widget output
            if "table" not in context:
                table = table_to_output(widget, control)
                context["table"] = RequestConfig(
                    request,
                ).configure(table)
        elif widget.kind == Widget.Kind.METRIC:
            metric = metric_to_output(widget, control)
            if widget.compare_previous_period and (
                used_control := widget.control if widget.has_control else control
            ):
                previous_metric = metric_to_output(widget, control, True)
                context["change"] = (metric - previous_metric) / previous_metric * 100
                context["period"] = DATETIME_FILTERS[used_control.date_range][
                    "previous_label"
                ]

            context["metric"] = metric
        else:
            chart, chart_id = chart_to_output(widget, control)
            context.update(chart)
            context["chart_id"] = chart_id


class WidgetName(TurboFrameUpdateView):
    model = Widget
    fields = ("name",)
    template_name = "widgets/name.html"
    turbo_frame_dom_id = "widget-editable-name"

    def get_success_url(self) -> str:
        return reverse(
            "widgets:name",
            args=(self.object.id,),
        )


class WidgetUpdate(DashboardMixin, TurboFrameFormsetUpdateView):
    model = Widget
    turbo_frame_dom_id = "widget-modal"

    def get_template_names(self):
        if self.object.kind == Widget.Kind.IFRAME:
            return "widgets/update-simple.html"
        if self.object.kind == Widget.Kind.IMAGE:
            return "widgets/update-simple.html"

        return "widgets/update.html"

    def get_form_class(self):
        return FORMS[self.request.POST.get("kind") or self.object.kind]

    def get_formset_kwargs(self, formset):
        kind = self.request.POST.get("kind") or self.object.kind
        if kind == Widget.Kind.SCATTER:
            return {"names": ["X", "Y"]}
        if kind == Widget.Kind.BUBBLE:
            return {"names": ["X", "Y", "Z"]}
        return {}

    def get_formset_form_kwargs(self, formset):
        table = self.request.POST.get("table") or getattr(self.object, "table")
        formset_kwargs = {}
        if table is not None:
            formset_kwargs["schema"] = (
                table if isinstance(table, Table) else Table.objects.get(pk=table)
            ).schema
        return formset_kwargs

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.dashboard.project
        return kwargs

    def get_success_url(self) -> str:
        import logging

        logger = logging.getLogger()

        logger.critical("what teh fuck is gong on")
        logger.critical(self.request.POST.get("submit"))
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

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.object.kind == Widget.Kind.TEXT:
            pass
        elif self.object.kind == Widget.Kind.IFRAME:
            pass
        elif self.object.kind == Widget.Kind.IMAGE:
            pass
        else:
            context["show_date_column"] = bool(
                context["form"].get_live_field("date_column")
            )
            context["styleForm"] = WidgetStyleForm(instance=self.object)

        return context

    def form_valid(self, form):
        r = super().form_valid(form)

        import logging

        logger = logging.getLogger()

        logger.critical("form wtf")
        logger.critical(form)
        logger.critical(form.instance)
        logger.critical(form.instance.image)

        analytics.track(
            self.request.user.id,
            WIDGET_CONFIGURED_EVENT,
            {
                "id": form.instance.id,
                "dashboard_id": self.dashboard.id,
                "type": form.instance.kind,
            },
        )
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
                self.page.control if self.page.has_control else None,
            )
            if self.object.error:
                self.object.error = None
        except Exception as e:
            error = error_name_to_snake(e)
            self.object.error = error
            if not template_exists(f"widgets/errors/{error}.html"):
                logging.warning(e, exc_info=e)
                honeybadger.notify(e)

        if self.request.POST.get("submit") == "Save & Preview":
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

        return TurboStreamResponse(
            [
                TurboStream(f"widgets-output-{self.object.id}-stream")
                .replace.template("widgets/output.html", context)
                .render(request=self.request),
                TurboStream(f"widget-name-{self.object.id}-stream")
                .replace.template(
                    "widgets/_widget_title.html", {"object": self.get_object}
                )
                .render(),
            ]
        )

    def form_invalid(self, form):
        r = super().form_invalid(form)
        if self.request.POST.get("close"):
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
                    self.page.control if self.page.has_control else None,
                )
                if self.object.error:
                    self.object.error = None
            except Exception as e:
                error = error_name_to_snake(e)
                self.object.error = error
                if not template_exists(f"widgets/errors/{error}.html"):
                    logging.warning(e, exc_info=e)
                    honeybadger.notify(e)

            return TurboStreamResponse(
                [
                    TurboStream(f"widgets-output-{self.object.id}-stream")
                    .replace.template("widgets/output.html", context)
                    .render(request=self.request),
                    TurboStream(f"widget-name-{self.object.id}-stream")
                    .replace.template(
                        "widgets/_widget_title.html", {"object": self.get_object}
                    )
                    .render(),
                ]
            )
        return r


class WidgetStyle(DashboardMixin, TurboFrameUpdateView):
    template_name = "widgets/update.html"
    model = Widget
    turbo_frame_dom_id = "widget-modal-style"
    form_class = WidgetStyleForm

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
                self.page.control if self.page.has_control else None,
            )
            if self.object.error:
                self.object.error = None
        except Exception as e:
            error = error_name_to_snake(e)
            self.object.error = error
            if not template_exists(f"widgets/errors/{error}.html"):
                logging.warning(e, exc_info=e)
                honeybadger.notify(e)

        if self.request.POST.get("submit") == "Save & Preview":
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

        return TurboStreamResponse(
            [
                TurboStream(f"widgets-output-{self.object.id}-stream")
                .replace.template("widgets/output.html", context)
                .render(request=self.request),
                TurboStream(f"widget-name-{self.object.id}-stream")
                .replace.template(
                    "widgets/_widget_title.html", {"object": self.get_object}
                )
                .render(),
            ]
        )

    def get_success_url(self) -> str:
        if self.request.POST.get("submit") == "Save & Preview":
            return "{}?{}".format(
                reverse(
                    "dashboard_widgets:update",
                    args=(
                        self.project.id,
                        self.dashboard.id,
                        self.object.id,
                    ),
                ),
                "show_style=True",
            )
        return "{}?{}".format(
            reverse(
                "project_dashboards:detail",
                args=(self.project.id, self.dashboard.id),
            ),
            "show_style=True",
        )


class WidgetOutput(DashboardMixin, SingleTableMixin, TurboFrameDetailView):
    template_name = "widgets/output.html"
    model = Widget
    paginate_by = 15

    def get_turbo_frame_dom_id(self):
        return f"widgets-output-{self.object.id}"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.dashboard.project
        try:
            add_output_context(
                context,
                self.object,
                self.request,
                self.page.control if self.page.has_control else None,
            )
        except Exception as e:
            error_template = f"widgets/errors/{error_name_to_snake(e)}.html"
            if template_exists(error_template):
                context["error_template"] = error_template
            else:
                context["error_template"] = "widgets/errors/default.html"

        return context

    def get_table(self, **kwargs):
        if self.object.is_valid and self.object.kind == Widget.Kind.TABLE:
            table = table_to_output(
                self.object,
                self.page.control if self.page.has_control else None,
            )
            return RequestConfig(
                self.request, paginate=self.get_table_pagination(table)
            ).configure(table)
        return type("DynamicTable", (DjangoTable,), {})(data=[])
