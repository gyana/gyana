from functools import cached_property

from .models import Dashboard


class DashboardMixin:
    @cached_property
    def dashboard(self):
        return Dashboard.objects.get(pk=self.kwargs["dashboard_id"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["dashboard"] = self.dashboard
        return context
