from urllib.parse import urlparse

from apps.dashboards.models import Dashboard
from django.db.models.query import QuerySet
from django.urls import resolve, reverse
from django.views.generic import DetailView, ListView
from django.views.generic.edit import DeleteView
from lib.bigquery import query_widget
from lib.chart import to_chart
from turbo_response.views import TurboCreateView, TurboUpdateView

from .forms import WidgetConfigForm, WidgetForm
from .models import Widget


class DashboardMixin:
    @property
    def dashboard(self):
        resolver_match = resolve(urlparse(self.request.META["HTTP_REFERER"]).path)
        return Dashboard.objects.get(pk=resolver_match.kwargs["pk"])


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

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["project"] = self.dashboard.project
        return kwargs

    def get_initial(self):
        initial = super().get_initial()
        initial["dashboard"] = self.dashboard
        return initial

    def get_success_url(self) -> str:
        return reverse("widgets:list")


class WidgetDetail(DetailView):
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
        return reverse("widgets:list")


class WidgetDelete(DeleteView):
    template_name = "widgets/delete.html"
    model = Widget

    def get_success_url(self) -> str:
        return reverse("widgets:list")


# Turbo frames


class WidgetConfig(TurboUpdateView):
    template_name = "widgets/config.html"
    model = Widget
    form_class = WidgetConfigForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["columns"] = [(name, name) for name in self.object.table.get_schema()]
        return kwargs

    def get_success_url(self) -> str:
        return reverse("widgets:config", args=(self.object.id,))


class WidgetOutput(DetailView):
    template_name = "widgets/output.html"
    model = Widget

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        if self.object.is_valid():
            df = query_widget(self.object)
            chart = to_chart(df, self.object)
            context_data["chart"] = chart.render()

        return context_data
