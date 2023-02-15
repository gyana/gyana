import analytics
from django.contrib import messages
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.crypto import get_random_string
from django.views.generic import DeleteView, DetailView
from invitations.adapters import get_invitations_adapter
from invitations.views import AcceptInvite, accept_invitation

from apps.base.analytics import INVITE_SENT_EVENT
from apps.base.views import CreateView, UpdateView
from apps.teams.mixins import TeamMixin

from .forms import InviteForm, InviteUpdateForm
from .models import Invite

# Modified from SendInvite view
# https://github.com/bee-keeper/django-invitations/blob/master/invitations/views.py


class InviteCreate(TeamMixin, CreateView):
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


class InviteUpdate(TeamMixin, UpdateView):
    template_name = "invites/update.html"
    model = Invite
    form_class = InviteUpdateForm

    def get_success_url(self) -> str:
        return reverse("team_invites:list", args=(self.team.id,))


class InviteDelete(TeamMixin, DeleteView):
    template_name = "invites/delete.html"
    model = Invite

    def get_success_url(self) -> str:
        return reverse("team_members:list", args=(self.team.id,))


# patch AcceptInvite in django-invitations
# - remove INVITATIONS_GONE_ON_ACCEPT_ERROR option
# - authenticated user: accept invite, redirect to team
# - anonymous user: redirect to signup, automatically accept afterwards (ACCEPT_INVITE_AFTER_SIGNUP=True)


original_post = AcceptInvite.post


def post(self, *args, **kwargs):
    self.object = invitation = self.get_object()

    # No invitation was found.
    if not invitation:
        get_invitations_adapter().add_message(
            self.request, messages.ERROR, "invitations/messages/invite_invalid.txt"
        )
        return redirect(self.get_signup_redirect())

    # The invitation was previously accepted, redirect to the login
    # view.
    if invitation.accepted:
        get_invitations_adapter().add_message(
            self.request,
            messages.ERROR,
            "invitations/messages/invite_already_accepted.txt",
            {"email": invitation.email},
        )
        return redirect(self.get_signup_redirect())

    # The key was expired.
    if invitation.key_expired():
        get_invitations_adapter().add_message(
            self.request,
            messages.ERROR,
            "invitations/messages/invite_expired.txt",
            {"email": invitation.email},
        )
        return redirect(self.get_signup_redirect())

    if self.request.user.is_authenticated:
        if self.request.user.email == self.object.email:
            accept_invitation(
                invitation=self.object,
                request=self.request,
                signal_sender=self.__class__,
            )
        else:
            get_invitations_adapter().add_message(
                self.request,
                messages.ERROR,
                "invitations/messages/invite_invalid_email.txt",
            )
        return redirect("teams:detail", self.object.team.id)

    if invitation.user_email_exists:
        return redirect(f'{reverse("account_login")}?next={self.request.path}')

    get_invitations_adapter().stash_verified_email(self.request, invitation.email)
    return redirect(self.get_signup_redirect())


AcceptInvite.post = post
