from apps.teams.invitations import send_invitation
from apps.teams.mixins import TeamMixin
from django.urls import reverse, reverse_lazy
from django.views.generic import DetailView
from django.views.generic.edit import DeleteView
from django_tables2 import SingleTableView
from turbo_response.views import TurboCreateView, TurboUpdateView

from .forms import InviteForm
from .models import Invite
from .tables import InviteTable


class InviteList(TeamMixin, SingleTableView):
    template_name = "invites/list.html"
    model = Invite
    table_class = InviteTable
    paginate_by = 20


class InviteCreate(TeamMixin, TurboCreateView):
    template_name = "invites/create.html"
    model = Invite
    form_class = InviteForm
    success_url = reverse_lazy("teams:team_invites:list")

    def form_valid(self, form):
        form.instance.invited_by = self.request.user
        form.instance.team = self.team
        form.save()

        send_invitation(form.instance)

        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse("teams:team_invites:list", args=(self.team.id,))


class InviteDetail(TeamMixin, DetailView):
    template_name = "invites/detail.html"
    model = Invite


class InviteUpdate(TeamMixin, TurboUpdateView):
    template_name = "invites/update.html"
    model = Invite
    form_class = InviteForm
    success_url = reverse_lazy("teams:team_invites:list")

    def get_success_url(self) -> str:
        return reverse("teams:team_invites:list", args=(self.team.id,))


class InviteDelete(TeamMixin, DeleteView):
    template_name = "invites/delete.html"
    model = Invite

    def get_success_url(self) -> str:
        return reverse("teams:team_invites:list", args=(self.team.id,))
