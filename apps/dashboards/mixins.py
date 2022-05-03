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
        return context


class PageMixin(DashboardMixin):
    @cached_property
    def page(self):
        return self.dashboard.pages.get(
            position=self.request.GET.get("dashboardPage", 1)
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["page"] = self.page
        return context
