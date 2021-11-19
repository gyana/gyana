from django.urls import reverse, reverse_lazy
from django.utils.functional import cached_property
from django.views.generic import DetailView, ListView
from django.views.generic.edit import DeleteView
from django_tables2 import SingleTableView

from apps.base.frames import (
    TurboFrameCreateView,
    TurboFrameDetailView,
    TurboFrameUpdateView,
)
from apps.base.turbo import TurboUpdateView

from .forms import DateSlicerForm
from .models import DateSlicer


class DateSlicerCreate(TurboFrameCreateView):
    template_name = "dateslicers/create.html"
    model = DateSlicer
    form_class = DateSlicerForm
    turbo_frame_dom_id = "dateslicers:create"

    @cached_property
    def dashboard(self):
        from apps.dashboards.models import Dashboard

        return Dashboard.objects.get(pk=self.request.POST["dashboard_id"])

    def form_valid(self, form):
        r = super().form_valid(form)
        self.dashboard.date_slicer = form.instance
        self.dashboard.save()

        return r

    def get_success_url(self) -> str:
        return reverse("dateslicers:detail", args=(self.object.id,))


class DateSlicerDetail(TurboFrameDetailView):
    template_name = "dateslicers/detail.html"
    model = DateSlicer
    turbo_frame_dom_id = "dateslicers:create"


class DateSlicerUpdate(TurboFrameUpdateView):
    template_name = "dateslicers/update.html"
    model = DateSlicer
    form_class = DateSlicerForm
    turbo_frame_dom_id = "dateslicers:update"

    def get_success_url(self) -> str:
        return reverse("dateslicers:update", args=(self.object.id,))


class DateSlicerDelete(DeleteView):
    template_name = "dateslicers/delete.html"
    model = DateSlicer
    success_url = reverse_lazy("dateslicers:list")
