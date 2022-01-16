from datetime import timezone

import analytics
from django.db.models.query import QuerySet
from django.http.response import HttpResponseRedirect
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.views.generic import DetailView
from django.views.generic.edit import DeleteView
from django_tables2 import SingleTableView

from apps.base.analytics import INVITE_SENT_EVENT
from apps.base.frames import TurboFrameListView
from apps.base.views import TurboCreateView, TurboUpdateView
from apps.teams.mixins import TeamMixin

from .forms import InviteForm, InviteUpdateForm
from .models import Invite
from .tables import InviteTable


class InviteList(TeamMixin, SingleTableView, TurboFrameListView):
    template_name = "invites/list.html"
    model = Invite
    table_class = InviteTable
    paginate_by = 20
    turbo_frame_dom_id = "team_invites:list"

    def get_queryset(self) -> QuerySet:
        return Invite.objects.filter(team=self.team, accepted=False)


# Modified from SendInvite view
# https://github.com/bee-keeper/django-invitations/blob/master/invitations/views.py


class InviteCreate(TeamMixin, TurboCreateView):
    template_name = "invites/create.html"
    model = Invite
    form_class = InviteForm

    def get_form_kwargs(self):
        return {**super().get_form_kwargs(), "team": self.team}

    def form_valid(self, form):
        form.instance.inviter = self.request.user
        form.instance.team = self.team
        form.instance.key = get_random_string(64).lower()
        form.save()

        form.instance.send_invitation(self.request)
        analytics.track(self.request.user.id, INVITE_SENT_EVENT)

        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse("team_members:list", args=(self.team.id,))


class InviteDetail(TeamMixin, DetailView):
    template_name = "invites/detail.html"
    model = Invite


class InviteUpdate(TeamMixin, TurboUpdateView):
    template_name = "invites/update.html"
    model = Invite
    form_class = InviteUpdateForm

    def get_success_url(self) -> str:
        return reverse("team_invites:list", args=(self.team.id,))


class InviteResend(TeamMixin, TurboUpdateView):
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


class InviteDelete(TeamMixin, DeleteView):
    template_name = "invites/delete.html"
    model = Invite

    def get_success_url(self) -> str:
        return reverse("team_members:list", args=(self.team.id,))
