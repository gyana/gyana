from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseRedirect, HttpResponse
from django.shortcuts import render, get_object_or_404
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_POST
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError

from .api_url_helpers import get_team_api_url_templates
from .decorators import login_and_team_required, team_admin_required
from .invitations import send_invitation, process_invitation, clear_invite_from_session
from .forms import TeamChangeForm
from .models import Team, Invitation
from .permissions import TeamAccessPermissions, TeamModelAccessPermissions
from .roles import is_admin, is_member
from .serializers import TeamSerializer, InvitationSerializer


@login_required
def manage_teams(request, path=""):
    return render(
        request, "teams/teams.html", {"api_urls": get_team_api_url_templates()}
    )


@login_required
def list_teams(request):
    teams = request.user.teams.all()
    return render(
        request,
        "teams/list_teams.html",
        {
            "teams": teams,
        },
    )


@login_required
def create_team(request):
    if request.method == "POST":
        form = TeamChangeForm(request.POST)
        if form.is_valid():
            team = form.save()
            team.members.add(request.user, through_defaults={"role": "admin"})
            team.save()
            return HttpResponseRedirect(reverse("teams:list_teams"))
    else:
        form = TeamChangeForm()
    return render(
        request,
        "teams/manage_team.html",
        {
            "form": form,
            "create": True,
        },
    )


@login_and_team_required
def manage_team_react(request, team_slug):
    team = request.team
    return render(
        request,
        "teams/manage_team_react.html",
        {
            "team": team,
            "team_json": TeamSerializer(team, context={"request": request}).data,
            "active_tab": "manage-team",
            "api_urls": get_team_api_url_templates(),
        },
    )


@login_and_team_required
def manage_team(request, team_slug):
    team = request.team
    if request.method == "POST":
        form = TeamChangeForm(request.POST, instance=team)
        if form.is_valid():
            form.save()
            return HttpResponseRedirect(reverse("teams:list_teams"))
    else:
        form = TeamChangeForm(instance=team)
    return render(
        request,
        "teams/manage_team.html",
        {
            "team": team,
            "form": form,
        },
    )


def accept_invitation(request, invitation_id):
    invitation = get_object_or_404(Invitation, id=invitation_id)
    if not invitation.is_accepted:
        # set invitation in the session in case needed later
        request.session["invitation_id"] = invitation_id
    else:
        clear_invite_from_session(request)
    return render(
        request,
        "teams/accept_invite.html",
        {
            "invitation": invitation,
        },
    )


@login_required
@require_POST
def accept_invitation_confirm(request, invitation_id):
    invitation = get_object_or_404(Invitation, id=invitation_id)
    if invitation.is_accepted:
        messages.error(
            request, _("Sorry, it looks like that invitation link has expired.")
        )
        return HttpResponseRedirect(reverse("web:home"))
    else:
        process_invitation(invitation, request.user)
        clear_invite_from_session(request)
        messages.success(
            request, _("You successfully joined {}").format(invitation.team.name)
        )
        return HttpResponseRedirect(
            reverse("web_team:home", args=[invitation.team.slug])
        )


class TeamViewSet(viewsets.ModelViewSet):
    queryset = Team.objects.all()
    serializer_class = TeamSerializer
    permission_classes = (TeamAccessPermissions,)

    def get_queryset(self):
        # filter queryset based on logged in user
        return self.request.user.teams.order_by("name")

    def perform_create(self, serializer):
        # ensure logged in user is set on the model during creation
        team = serializer.save()
        team.members.add(self.request.user, through_defaults={"role": "admin"})


class InvitationViewSet(viewsets.ModelViewSet):
    queryset = Invitation.objects.all()
    serializer_class = InvitationSerializer
    permission_classes = (TeamModelAccessPermissions,)

    @property
    def team(self):
        team = get_object_or_404(Team, slug=self.kwargs["team_slug"])
        if is_member(self.request.user, team):
            return team
        else:
            raise PermissionDenied()

    def _ensure_team_match(self, team):
        if team != self.team:
            raise ValidationError("Team set in invitation must match URL")

    def get_queryset(self):
        # filter queryset based on logged in user and team
        return self.queryset.filter(team=self.team)

    def perform_create(self, serializer):
        # ensure logged in user is set on the model during creation
        # and can access the underlying team
        team = serializer.validated_data["team"]
        self._ensure_team_match(team)

        # unfortunately, the permissions class doesn't handle creation well
        # https://www.django-rest-framework.org/api-guide/permissions/#limitations-of-object-level-permissions
        if not is_admin(self.request.user, team):
            raise PermissionDenied()

        invitation = serializer.save(invited_by=self.request.user)
        send_invitation(invitation)


@team_admin_required
def resend_invitation(request, team, invitation_id):
    invitation = get_object_or_404(Invitation, id=invitation_id)
    if invitation.team != request.team:
        raise ValueError(
            _("Request team {team} did not match invitation team {invite_team}").format(
                team=request.team.slug,
                invite_team=invitation.team.slug,
            )
        )
    send_invitation(invitation)
    return HttpResponse("Ok")
