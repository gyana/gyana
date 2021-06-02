from apps.dashboards.mixins import DashboardMixin
from apps.tables.models import Table
from apps.utils.formset_update_view import FormsetUpdateView
from apps.widgets.visuals import chart_to_output, table_to_output
from django.db import transaction
from django.db.models.query import QuerySet
from django.urls import reverse
from django.views.decorators.http import condition
from django.views.generic import DetailView, ListView
from django.views.generic.edit import DeleteView
from turbo_response.views import TurboCreateView

from .forms import FilterFormset, WidgetConfigForm
from .models import Widget


class WidgetList(DashboardMixin, ListView):
    template_name = "widgets/list.html"
    model = Widget
    paginate_by = 20

    def get_queryset(self) -> QuerySet:
        widgets = Widget.objects.filter(dashboard=self.dashboard).all()
        widget_dict = {widget.pk: widget for widget in widgets}
        return [widget_dict[idx] for idx in self.dashboard.sort_order]


class WidgetCreate(DashboardMixin, TurboCreateView):
    template_name = "widgets/create.html"
    model = Widget
    fields = []

    def form_valid(self, form):
        form.instance.dashboard = self.dashboard

        with transaction.atomic():
            response = super().form_valid(form)
            self.dashboard.sort_order.append(self.object.id)
            self.dashboard.save()

        return response

    def get_success_url(self) -> str:
        return reverse(
            "projects:dashboards:widgets:update",
            args=(
                self.project.id,
                self.dashboard.id,
                self.object.id,
            ),
        )


class WidgetDetail(DashboardMixin, DetailView):
    template_name = "widgets/detail.html"
    model = Widget


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
                "projects:dashboards:widgets:update",
                args=(
                    self.project.id,
                    self.dashboard.id,
                    self.object.id,
                ),
            )
        return reverse(
            "projects:dashboards:detail",
            args=(self.project.id, self.dashboard.id),
        )


class WidgetDelete(DashboardMixin, DeleteView):
    template_name = "widgets/delete.html"
    model = Widget

    def delete(self, request, *args, **kwargs):
        with transaction.atomic():
            self.dashboard.sort_order.remove(self.get_object().id)
            self.dashboard.save()
            response = super().delete(request, *args, **kwargs)

        return response

    def get_success_url(self) -> str:
        return reverse(
            "projects:dashboards:detail",
            args=(self.project.id, self.dashboard.id),
        )


# Turbo frames


def last_modified_widget_output(request, pk):
    widget = Widget.objects.get(pk=pk)
    return max(widget.updated, widget.table.data_updated)


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

        if self.object.is_valid:
            if self.object.kind == Widget.Kind.TABLE:
                context_data.update(table_to_output(self.object))
            else:
                context_data.update(chart_to_output(self.object))

        return context_data
