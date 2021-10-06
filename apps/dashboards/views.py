import analytics
from apps.base.analytics import DASHBOARD_CREATED_EVENT, DASHBOARD_DUPLICATED_EVENT
from apps.base.turbo import TurboCreateView, TurboUpdateView
from apps.dashboards.tables import DashboardTable
from apps.projects.mixins import ProjectMixin
from apps.widgets.models import WIDGET_CHOICES_ARRAY
from django.db.models.query import QuerySet
from django.http import HttpResponse
from django.shortcuts import redirect
from django.template import loader
from django.urls.base import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST
from django.views.generic.detail import DetailView
from django.views.generic.edit import DeleteView, FormView
from django_tables2 import SingleTableView

from .forms import DashboardCreateForm, DashboardForm, DashboardLoginForm
from .models import Dashboard


class DashboardList(ProjectMixin, SingleTableView):
    template_name = "dashboards/list.html"
    model = Dashboard
    table_class = DashboardTable
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        context_data["dashboard_count"] = Dashboard.objects.filter(
            project=self.project
        ).count()

        return context_data

    def get_queryset(self) -> QuerySet:
        return Dashboard.objects.filter(project=self.project).all()


class DashboardCreate(ProjectMixin, TurboCreateView):
    template_name = "dashboards/create.html"
    model = Dashboard
    form_class = DashboardCreateForm

    def get_initial(self):
        initial = super().get_initial()
        initial["project"] = self.project

        return initial

    def get_success_url(self) -> str:
        return reverse(
            "project_dashboards:detail", args=(self.project.id, self.object.id)
        )

    def form_valid(self, form):
        r = super().form_valid(form)

        analytics.track(
            self.request.user.id,
            DASHBOARD_CREATED_EVENT,
            {"id": form.instance.id, "name": form.instance.name},
        )

        return r


class DashboardDetail(ProjectMixin, TurboUpdateView):
    template_name = "dashboards/detail.html"
    model = Dashboard
    form_class = DashboardForm

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["choices"] = WIDGET_CHOICES_ARRAY

        return context_data

    def get_success_url(self) -> str:
        return reverse(
            "project_dashboards:detail", args=(self.project.id, self.object.id)
        )


class DashboardDelete(ProjectMixin, DeleteView):
    template_name = "dashboards/delete.html"
    model = Dashboard

    def get_success_url(self) -> str:
        return reverse("project_dashboards:list", args=(self.project.id,))


class DashboardDuplicate(TurboUpdateView):
    template_name = "components/_duplicate.html"
    model = Dashboard
    fields = []
    extra_context = {"object_name": "dashboard"}

    def form_valid(self, form):
        r = super().form_valid(form)

        clone = self.object.make_clone(
            attrs={
                "name": "Copy of " + self.object.name,
                "shared_id": None,
                "shared_status": Dashboard.SharedStatus.PRIVATE,
            }
        )

        clone.save()

        analytics.track(
            self.request.user.id,
            DASHBOARD_DUPLICATED_EVENT,
            {
                "id": form.instance.id,
            },
        )
        return r

    def get_success_url(self) -> str:
        return reverse("project_dashboards:list", args=(self.object.project.id,))


class DashboardPublic(DetailView):
    template_name = "dashboards/public.html"
    model = Dashboard

    def get_object(self):
        return self.kwargs["dashboard"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.object.project
        return context


class DashboardLogin(FormView):
    template_name = "dashboards/login.html"
    form_class = DashboardLoginForm

    @property
    def dashboard(self):
        return self.kwargs["dashboard"]

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["dashboard"] = self.dashboard
        return kwargs

    def form_valid(self, form):
        self.request.session[str(self.dashboard.shared_id)] = {
            "auth_success": True,
            "logged_in": timezone.now().isoformat(),
        }
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse("dashboards:public", args=(self.dashboard.shared_id,))
