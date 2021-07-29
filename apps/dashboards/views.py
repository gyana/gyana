import uuid

import analytics
from apps.dashboards.serializers import DashboardSerializer
from apps.dashboards.tables import DashboardTable
from apps.projects.mixins import ProjectMixin
from apps.utils.segment_analytics import (DASHBOARD_CREATED_EVENT,
                                          DASHBOARD_DUPLICATED_EVENT)
from apps.widgets.models import WIDGET_CHOICES_ARRAY
from django.db.models.query import QuerySet
from django.urls.base import reverse
from django.views.generic.detail import DetailView
from django.views.generic.edit import DeleteView
from django_tables2 import SingleTableView
from rest_framework import generics
from turbo_response.views import TurboCreateView, TurboUpdateView

from .forms import DashboardForm, DashboardFormCreate
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
    form_class = DashboardFormCreate

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
    template_name = "dashboards/duplicate.html"
    model = Dashboard
    fields = []

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


class DashboardShare(TurboUpdateView):
    template_name = "dashboards/share.html"
    model = Dashboard
    fields = []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        context["dont_hide_body"] = True
        return context

    def form_valid(self, form):
        r = super().form_valid(form)
        if self.object.shared_status == Dashboard.SharedStatus.PRIVATE:
            self.object.shared_status = Dashboard.SharedStatus.PUBLIC
            self.object.shared_id = self.object.shared_id or uuid.uuid4()
        else:
            self.object.shared_status = Dashboard.SharedStatus.PRIVATE
        self.object.save()
        return r

    def get_success_url(self) -> str:
        return reverse(
            "dashboards:share",
            args=(self.object.id,),
        )


class DashboardPublic(DetailView):
    template_name = "dashboards/public.html"
    model = Dashboard

    def get_object(self):
        return self.kwargs["dashboard"]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["project"] = self.object.project
        return context


# APIs


class DashboardSort(generics.UpdateAPIView):
    queryset = Dashboard.objects.all()
    serializer_class = DashboardSerializer
