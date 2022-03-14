from django.utils.functional import cached_property

from apps.projects.mixins import ProjectMixin

from .models import Dashboard


class DashboardMixin(ProjectMixin):
    @cached_property
    def dashboard(self):
        return Dashboard.objects.get(pk=self.kwargs["dashboard_id"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["dashboard"] = self.dashboard
        context["page"] = self.page
        return context

    @cached_property
    def page(self):
        """Make sure that the the dashboardPage argument is provided everytime
        a frame uses this property."""
        return self.dashboard.pages.get(
            position=self.request.GET.get("dashboardPage", 1)
        )
