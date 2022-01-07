import copy

import analytics
from django.db.models.query import QuerySet
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls.base import reverse
from django.utils import timezone
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache
from django.views.decorators.clickjacking import xframe_options_exempt
from django.views.decorators.debug import sensitive_post_parameters
from django.views.generic.base import TemplateView
from django.views.generic.detail import DetailView
from django.views.generic.edit import CreateView, DeleteView, FormView
from django_tables2 import SingleTableView
from turbo_response.response import HttpResponseSeeOther

from apps.base.analytics import (
    DASHBOARD_CREATED_EVENT,
    DASHBOARD_CREATED_EVENT_FROM_INTEGRATION,
    DASHBOARD_DUPLICATED_EVENT,
)
from apps.base.turbo import TurboCreateView, TurboUpdateView
from apps.dashboards.mixins import DashboardMixin
from apps.dashboards.tables import DashboardTable
from apps.integrations.models import Integration
from apps.projects.mixins import ProjectMixin
from apps.widgets.models import WIDGET_CHOICES_ARRAY, Widget

from .forms import DashboardCreateForm, DashboardLoginForm, DashboardNameForm
from .models import Dashboard, Page


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
        # Create page
        form.instance.pages.create()

        analytics.track(
            self.request.user.id,
            DASHBOARD_CREATED_EVENT,
            {"id": form.instance.id, "name": form.instance.name},
        )

        return r


class DashboardCreateFromIntegration(ProjectMixin, TurboCreateView):
    model = Dashboard
    template_name = "dashboards/create_from_integration.html"
    fields = ("project",)

    def get_success_url(self) -> str:
        return reverse(
            "project_dashboards:detail", args=(self.project.id, self.object.id)
        )

    def form_valid(self, form):
        r = super().form_valid(form)
        # Create page
        page = form.instance.pages.create()

        analytics.track(
            self.request.user.id,
            DASHBOARD_CREATED_EVENT_FROM_INTEGRATION,
            {"id": form.instance.id, "name": form.instance.name},
        )
        integration = get_object_or_404(
            Integration, pk=self.request.POST["integration"]
        )
        table = integration.table_set.first()
        page.widgets.create(
            kind=Widget.Kind.TABLE,
            name=f"Table from {integration.name}",
            table=table,
            x=0,
            y=0,
        )
        self.object.name = f"{integration.name} dashboard"
        self.object.name
        return r


class DashboardDetail(ProjectMixin, TurboUpdateView):
    template_name = "dashboards/detail.html"
    model = Dashboard
    form_class = DashboardNameForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["categories"] = Widget.Category.choices
        context["font_families"] = Dashboard.FontFamily.choices

        context["choices"] = WIDGET_CHOICES_ARRAY
        context["modal_item"] = self.request.GET.get("modal_item")
        page = self.object.pages.get(position=self.request.GET.get("page", 1))
        context["page"] = page
        context["page_count"] = self.object.pages.count()
        context["next_page"] = page.position + 1
        context["previous_page"] = page.position - 1
        return context

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


# This allows a shared dashboard to be embeded in an iFrame
@method_decorator(xframe_options_exempt, name="dispatch")
class DashboardPublic(DetailView):
    template_name = "dashboards/public.html"
    model = Dashboard

    def get_object(self):
        return self.kwargs["dashboard"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.object.project
        page = self.object.pages.get(position=self.request.GET.get("page", 1))
        context["page"] = page
        context["page_count"] = self.object.pages.count()
        context["next_page"] = page.position + 1
        context["previous_page"] = page.position - 1
        return context


class DashboardLogin(FormView):
    template_name = "dashboards/login.html"
    form_class = DashboardLoginForm

    @property
    def dashboard(self):
        return self.kwargs["dashboard"]

    @method_decorator(sensitive_post_parameters())
    @method_decorator(never_cache)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

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


class DashboardLogout(TemplateView):
    template_name = "dashboards/login.html"

    @property
    def dashboard(self):
        return self.kwargs["dashboard"]

    @method_decorator(never_cache)
    def dispatch(self, request, *args, **kwargs):
        del self.request.session[str(self.dashboard.shared_id)]

        return HttpResponseRedirect(
            reverse("dashboards:login", args=(self.dashboard.shared_id,))
        )


class PageCreate(DashboardMixin, CreateView):
    model = Page
    fields = []
    # Not used
    template_name = "dashboards/create.html"

    def form_valid(self, form):
        form.instance.dashboard = self.dashboard
        form.instance.position = self.dashboard.pages.count() + 1
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return f"{reverse('project_dashboards:detail', args=(self.project.id, self.dashboard.id))}?page={self.object.position}"


class PageDelete(DashboardMixin, DeleteView):
    model = Page
    fields = []
    # Not used
    template_name = "dashboards/delete.html"

    def delete(self, request, *args, **kwargs):
        page = self.get_object()
        # The delete button should be disabled for the last page but just in case
        # this will not delete but return the same page
        if page.position == 1:
            return HttpResponseRedirect(
                f"{reverse('project_dashboards:detail', args=(self.project.id, self.dashboard.id))}?page={page.position}"
            )
        r = super().delete(request, *args, **kwargs)

        for follow_page in self.dashboard.pages.filter(
            position__gt=page.position
        ).iterator():
            follow_page.position = follow_page.position - 1
            follow_page.save()

        return r

    def get_success_url(self) -> str:
        return f"{reverse('project_dashboards:detail', args=(self.project.id, self.dashboard.id))}?page={min(self.object.position, self.dashboard.pages.count()-1)}"
