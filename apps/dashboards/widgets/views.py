from apps.dashboards.mixins import DashboardMixin
from django.db.models.query import QuerySet
from django.urls import reverse
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
        return Widget.objects.filter(dashboard=self.dashboard).all()


class WidgetCreate(DashboardMixin, TurboCreateView):
    template_name = "widgets/create.html"
    model = Widget
    form_class = WidgetForm

    def get_initial(self):
        initial = super().get_initial()
        initial["dashboard"] = self.dashboard
        return initial

    def get_success_url(self) -> str:
        return reverse("dashboards:widgets:list", args=(self.dashboard.id,))


class WidgetDetail(DashboardMixin, DetailView):
    template_name = "widgets/detail.html"
    model = Widget


class WidgetUpdate(DashboardMixin, TurboUpdateView):
    template_name = "widgets/update.html"
    model = Widget
    form_class = WidgetForm

    def get_success_url(self) -> str:
        return reverse("dashboards:widgets:list", args=(self.dashboard.id,))


class WidgetDelete(DashboardMixin, DeleteView):
    template_name = "widgets/delete.html"
    model = Widget

    def get_success_url(self) -> str:
        return reverse("dashboards:widgets:list", args=(self.dashboard.id,))


# Turbo frames


class WidgetConfig(DashboardMixin, TurboUpdateView):
    template_name = "widgets/config.html"
    model = Widget
    form_class = WidgetConfigForm

    def get_success_url(self) -> str:
        return reverse(
            "dashboards:widgets:config", args=(self.dashboard.id, self.object.id)
        )
