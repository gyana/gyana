from django.conf import settings
from django.urls import reverse_lazy
from django.urls.base import reverse
from django.views.generic.edit import DeleteView

from apps.base.views import TurboCreateView
from apps.teams.mixins import TeamMixin

from .forms import CNameForm
from .models import CName


class CNameCreate(TeamMixin, TurboCreateView):
    template_name = "cnames/create.html"
    model = CName
    form_class = CNameForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["team"] = self.team
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["cname_domain"] = settings.CNAME_DOMAIN
        return context

    def get_success_url(self) -> str:
        return reverse("teams:update", args=(self.team.id,))


class CNameDelete(TeamMixin, DeleteView):
    template_name = "cnames/delete.html"
    model = CName

    def get_success_url(self) -> str:
        return reverse("teams:update", args=(self.team.id,))
