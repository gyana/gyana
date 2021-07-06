import http

from django import forms
from django.contrib import messages
from django.db.models.query import QuerySet
from django.http.response import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse, reverse_lazy
from django.utils.crypto import get_random_string
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DetailView
from django.views.generic.edit import DeleteView, FormView
from django_tables2 import SingleTableView
from turbo_response.views import TurboCreateView, TurboFormView, TurboUpdateView

from apps.teams.mixins import TeamMixin

from .forms import InviteForm
from .invitations import clear_invite_from_session, process_invitation, send_invitation
from .models import Invite
from .tables import InviteTable


class InviteList(TeamMixin, SingleTableView):
    template_name = "invites/list.html"
    model = Invite
    table_class = InviteTable
    paginate_by = 20

    def get_queryset(self) -> QuerySet:
        return Invite.objects.filter(team=self.team)


# class InviteCreate(TeamMixin, TurboFormView):
#     template_name = "invites/create.html"
#     form_class = InviteForm

#     def form_valid(self, form):
#         email = form.cleaned_data["email"]

#         try:
#             invite = form.save(email, self.team)
#             invite.inviter = self.request.user
#             invite.save()
#             invite.send_invitation(self.request)

#         except Exception:
#             return self.form_invalid(form)
#         return self.render_to_response(
#             self.get_context_data(
#                 success_message=_("%(email)s has been invited") % {"email": email}
#             )
#         )

#     def form_invalid(self, form: forms.Form):
#         return self.render_to_response(self.get_context_data(form=form))

# Modified from SendInvite view
# https://github.com/bee-keeper/django-invitations/blob/master/invitations/views.py


class InviteCreate(TeamMixin, TurboCreateView):
    template_name = "invites/create.html"
    model = Invite
    form_class = InviteForm
    success_url = reverse_lazy("teams:team_invites:list")

    def form_valid(self, form):
        form.instance.inviter = self.request.user
        form.instance.team = self.team
        form.instance.key = get_random_string(64).lower()
        form.save()

        form.instance.send_invitation(self.request)

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


# class InviteAccept(DetailView):
#     template = "invites/accept.html"
#     model = Invite

#     def get_context_data(self, **kwargs):
#         context = super().get_context_data(**kwargs)

#         if not self.object.is_accepted:
#             # set invitation in the session in case needed later
#             self.request.session["invitation_id"] = self.object.id
#         else:
#             clear_invite_from_session(self.request)

#         return context


# # @login_required
# # @require_POST
# def accept_invitation_confirm(request, invitation_id):
#     invitation = get_object_or_404(Invite, id=invitation_id)
#     if invitation.is_accepted:
#         messages.error(
#             request, _("Sorry, it looks like that invitation link has expired.")
#         )
#         return HttpResponseRedirect(reverse("web:home"))
#     else:
#         process_invitation(invitation, request.user)
#         clear_invite_from_session(request)
#         messages.success(
#             request, _("You successfully joined {}").format(invitation.team.name)
#         )
#         return HttpResponseRedirect(reverse("teams:detail", args=[invitation.team.id]))


# # @team_admin_required
# def resend_invitation(request, team, invitation_id):
#     invitation = get_object_or_404(Invite, id=invitation_id)
#     if invitation.team != request.team:
#         raise ValueError(
#             _("Request team {team} did not match invitation team {invite_team}").format(
#                 team=request.team.slug,
#                 invite_team=invitation.team.slug,
#             )
#         )
#     send_invitation(invitation)
#     return HttpResponse("Ok")
