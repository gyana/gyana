import logging

import analytics
from apps.base.analytics import WIDGET_CONFIGURED_EVENT
from apps.base.frames import (
    TurboFrameDetailView,
    TurboFrameFormsetUpdateView,
    TurboFrameListView,
    TurboFrameUpdateView,
)
from apps.base.table_data import RequestConfig
from apps.dashboards.mixins import DashboardMixin
from apps.tables.models import Table
from apps.widgets.visuals import chart_to_output, table_to_output
from django.db.models.query import QuerySet
from django.urls import reverse
from django_tables2.tables import Table as DjangoTable
from django_tables2.views import SingleTableMixin
from turbo_response import TurboStream
from turbo_response.response import TurboStreamResponse

from .forms import FORMS
from .models import WIDGET_CHOICES_ARRAY, Widget


def add_output_context(context, widget, request):
    if widget.is_valid:
        if widget.kind == Widget.Kind.TEXT:
            pass
        elif widget.kind == Widget.Kind.TABLE:
            # avoid duplicating work for widget output
            if "table" not in context:
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
        modal_item = self.request.GET.get("modal_item")
        context_data["modal_item"] = int(modal_item) if modal_item else modal_item
        return context_data

    def get_queryset(self) -> QuerySet:
        return Widget.objects.filter(dashboard=self.dashboard)


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
    template_name = "widgets/update.html"
    model = Widget
    turbo_frame_dom_id = "widget-modal"

    def get_form_class(self):
        return FORMS[self.request.POST.get("kind") or self.object.kind]

    def get_formset_kwargs(self, formset):
        table = self.request.POST.get("table") or getattr(self.object, "table")
        if table is not None:
            return {
                "schema": (
                    table if isinstance(table, Table) else Table.objects.get(pk=table)
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
            add_output_context(context, self.object, self.request)
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
