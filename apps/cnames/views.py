from apps.base.turbo import TurboCreateView, TurboUpdateView
from apps.teams.mixins import TeamMixin
from django.urls import reverse_lazy
from django.urls.base import reverse
from django.views.generic import DetailView, ListView
from django.views.generic.edit import DeleteView
from django_tables2 import SingleTableView

from .forms import CNameForm
from .models import CName
from .tables import CNameTable


class CNameList(SingleTableView):
    template_name = "cnames/list.html"
    model = CName
    table_class = CNameTable
    paginate_by = 20


class CNameCreate(TeamMixin, TurboCreateView):
    template_name = "cnames/create.html"
    model = CName
    form_class = CNameForm
    success_url = reverse_lazy("cnames:list")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["team"] = self.team
        return kwargs

    def get_success_url(self) -> str:
        return reverse("teams:update", args=(self.team.id,))


class CNameDetail(DetailView):
    template_name = "cnames/detail.html"
    model = CName


class CNameUpdate(TurboUpdateView):
    template_name = "cnames/update.html"
    model = CName
    form_class = CNameForm
    success_url = reverse_lazy("cnames:list")


class CNameDelete(TeamMixin, DeleteView):
    template_name = "cnames/delete.html"
    model = CName

    def get_success_url(self) -> str:
        return reverse("teams:update", args=(self.team.id,))
