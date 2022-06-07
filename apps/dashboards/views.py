import analytics
from django.db.models.query import QuerySet
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect
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

from apps.base.analytics import (
    DASHBOARD_CREATED_EVENT,
    DASHBOARD_CREATED_EVENT_FROM_INTEGRATION,
    DASHBOARD_DUPLICATED_EVENT,
)
from apps.base.views import TurboCreateView, TurboUpdateView
from apps.dashboards.mixins import DashboardMixin, PageMixin
from apps.dashboards.tables import DashboardTable
from apps.integrations.models import Integration
from apps.projects.mixins import ProjectMixin
from apps.widgets.models import WIDGET_CHOICES_ARRAY, Widget

from .forms import DashboardCreateForm, DashboardLoginForm, DashboardNameForm
from .models import Dashboard, DashboardUpdate, DashboardVersion, Page


class DashboardList(ProjectMixin, SingleTableView):
    template_name = "dashboards/list.html"
    model = Dashboard
    table_class = DashboardTable
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        context_data["object_name"] = "dashboard"
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
        # Create page and first update entry
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
        page = self.object.pages.get(position=self.request.GET.get("dashboardPage", 1))
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
                "name": f"Copy of {self.object.name}",
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
    model = Dashboard

    def get_template_names(self):
        if self.request.GET.get("printPreview"):
            return "dashboards/print.html"

        return "dashboards/public.html"

    def get_object(self):
        return self.kwargs["dashboard"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.object.project
        page = self.object.pages.get(position=self.request.GET.get("dashboardPage", 1))
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


class PageCreate(PageMixin, CreateView):
    model = Page
    fields = []
    # Not used
    template_name = "dashboards/create.html"

    def form_valid(self, form):
        form.instance.dashboard = self.dashboard
        form.instance.position = self.dashboard.pages.count() + 1
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return f"{reverse('project_dashboards:detail', args=(self.project.id, self.dashboard.id))}?dashboardPage={self.object.position}"


class PageDelete(PageMixin, DeleteView):
    model = Page
    fields = []
    # Not used
    template_name = "dashboards/delete.html"

    def form_valid(self, form):
        # The delete button should be disabled for the last page but just in case
        # this will not delete but return the same page
        if self.object.position == 1:
            return HttpResponseRedirect(
                f"{reverse('project_dashboards:detail', args=(self.project.id, self.dashboard.id))}?dashboardPage={self.object.position}"
            )

        return super().form_valid(form)

    def get_success_url(self) -> str:
        return f"{reverse('project_dashboards:detail', args=(self.project.id, self.dashboard.id))}?dashboardPage={min(self.object.position, self.dashboard.pages.count()-1)}"


class DashboardRestore(TurboUpdateView):
    model = DashboardVersion
    fields = []
    template_name = "components/dummy.html"

    def form_valid(self, form):
        instance = form.instance
        instance.dashboard.restore_as_of(instance.created)
        instance.dashboard.updates.create(content_object=instance.dashboard)

        return redirect(
            reverse(
                "project_dashboards:detail",
                args=(instance.dashboard.project.id, instance.dashboard.id),
            )
        )


class DashboardUpdateRestore(DashboardRestore):
    model = DashboardUpdate


class PageMove(PageMixin, TurboUpdateView):
    model = Page
    fields = []
    template_name = "dashboards/forms/move_page.html"

    def form_valid(self, form):
        page = self.get_object()
        destination = int(form.data["position"])

        if page.position == destination:
            return HttpResponseRedirect(self.get_success_url())

        if page.position < destination:
            following_pages = list(
                self.dashboard.pages.filter(
                    position__gt=page.position, position__lte=destination
                )
            )

            for dashboard_page in following_pages:
                dashboard_page.position = dashboard_page.position - 1

            page.position = destination
            Page.objects.bulk_update(following_pages + [page], ["position"])

        elif page.position > destination:
            preceding_pages = list(
                self.dashboard.pages.filter(
                    position__gte=destination, position__lt=page.position
                )
            )

            for dashboard_page in preceding_pages:
                dashboard_page.position = dashboard_page.position + 1

            page.position = destination
            Page.objects.bulk_update(preceding_pages + [page], ["position"])

        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        return f"{reverse('project_dashboards:detail', args=(self.project.id, self.dashboard.id),)}?dashboardPage={self.get_object().position}"


class PageName(PageMixin, TurboUpdateView):
    model = Page
    fields = ["name"]
    template_name = "dashboards/forms/name_page.html"

    @property
    def page(self):
        # Doesnt take the page parameter
        return self.object

    def get_success_url(self) -> str:
        return reverse(
            "project_dashboards:page-name",
            args=(self.project.id, self.dashboard.id, self.page.id),
        )
