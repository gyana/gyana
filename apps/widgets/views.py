from apps.dashboards.mixins import DashboardMixin
from apps.widgets.visuals import VISUAL_TO_OUTPUT
from django.db import transaction
from django.db.models.query import QuerySet
from django.urls import reverse
from django.views.decorators.http import condition
from django.views.generic import DetailView, ListView
from django.views.generic.edit import DeleteView
from turbo_response.views import TurboCreateView, TurboUpdateView

from .forms import WidgetConfigForm, WidgetForm
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
    form_class = WidgetForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.dashboard.project
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        initial["dashboard"] = self.dashboard
        return initial

    def form_valid(self, form):
        with transaction.atomic():
            response = super().form_valid(form)
            self.dashboard.sort_order.append(self.object.id)
            self.dashboard.save()

        return response

    def get_success_url(self) -> str:
        return reverse(
            "projects:dashboards:widgets:detail",
            args=(
                self.project.id,
                self.dashboard.id,
                self.object.id,
            ),
        )


class WidgetDetail(DashboardMixin, DetailView):
    template_name = "widgets/detail.html"
    model = Widget


class WidgetUpdate(DashboardMixin, TurboUpdateView):
    template_name = "widgets/update.html"
    model = Widget
    form_class = WidgetForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.dashboard.project
        return kwargs

    def get_success_url(self) -> str:
        return reverse(
            "projects:dashboards:widgets:list",
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
            "projects:dashboards:widgets:list",
            args=(self.project.id, self.dashboard.id),
        )


# Turbo frames


class WidgetConfig(TurboUpdateView):
    template_name = "widgets/config.html"
    model = Widget
    form_class = WidgetConfigForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["columns"] = [(name, name) for name in self.object.table.schema]
        return kwargs

    def get_success_url(self) -> str:
        return reverse("widgets:config", args=(self.object.id,))


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

        if self.object.is_valid():
            context_data.update(VISUAL_TO_OUTPUT[self.object.visual_kind](self.object))

        return context_data
