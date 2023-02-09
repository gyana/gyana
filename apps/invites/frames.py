from django.db.models.query import QuerySet
from django.http.response import HttpResponseRedirect
from django.urls import reverse
from django.views.generic import ListView, UpdateView
from django_tables2 import SingleTableView

from apps.teams.mixins import TeamMixin

from .models import Invite
from .tables import InviteTable


class InviteList(TeamMixin, SingleTableView, ListView):
    template_name = "invites/list.html"
    model = Invite
    table_class = InviteTable
    paginate_by = 20

    def get_queryset(self) -> QuerySet:
        return Invite.objects.filter(team=self.team, accepted=False)


class InviteResend(TeamMixin, UpdateView):
    template_name = "invites/resend.html"
    model = Invite
    fields = []

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["record"] = context["object"]
        return context

    def form_valid(self, form):
        self.get_object().send_invitation(self.request)
        # Don't save the form
        return HttpResponseRedirect(self.get_success_url())

    def get_success_url(self) -> str:
        return reverse("team_invites:resend", args=(self.team.id, self.object.id))
