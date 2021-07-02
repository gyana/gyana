from apps.utils.table import NaturalDatetimeColumn
from apps.users.models import CustomUser
from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.decorators.http import require_POST
from django.views.generic import DetailView, DeleteView, UpdateView
from django_tables2 import Column, Table
from rest_framework import viewsets
from rest_framework.exceptions import PermissionDenied, ValidationError
from turbo_response.views import TurboCreateView

from .api_url_helpers import get_team_api_url_templates
from .decorators import login_and_team_required, team_admin_required
from .forms import TeamChangeForm
from .invitations import clear_invite_from_session, process_invitation, send_invitation
from .models import Invitation, Team
from .permissions import TeamAccessPermissions, TeamModelAccessPermissions
from .roles import is_admin, is_member
from .serializers import InvitationSerializer, TeamSerializer
from apps.projects.models import Project



class TeamCreate(LoginRequiredMixin, TurboCreateView):
    model = Team
    form_class = TeamChangeForm
    template_name = "teams/create.html"

    def form_valid(self, form: forms.Form) -> HttpResponse:
        form.save()
        form.instance.members.add(self.request.user, through_defaults={"role": "admin"})

        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse("teams:detail", args=(self.object.slug,))


class TeamUpdate(LoginRequiredMixin, UpdateView):
    template_name = "teams/settings.html"
    model = Team

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        return context_data

    def get_form_class(self):
        return TeamChangeForm

    def get_success_url(self) -> str:
        return reverse("teams:settings", args=(self.object.slug,))


class TeamDelete(LoginRequiredMixin, DeleteView):
    template_name = "teams/delete.html"
    model = Team

    def get_success_url(self) -> str:
        return reverse("web:home")


class TeamProjectsTable(Table):
    class Meta:
        model = Project
        attrs = {"class": "table"}
        fields = (
            "name",
            "integration_count",
            "workflow_count",
            "dashboard_count",
            "created",
            "updated",
        )

    name = Column(linkify=True)
    created = NaturalDatetimeColumn()
    updated = NaturalDatetimeColumn()
    integration_count = Column(verbose_name="Integrations")
    workflow_count = Column(verbose_name="Workflows")
    dashboard_count = Column(verbose_name="Dashboards")


class TeamDetail(DetailView):
    template_name = "teams/detail.html"
    model = Team

    def get_context_data(self, **kwargs):
        from apps.projects.models import Project

        context = super().get_context_data(**kwargs)
        context["team_projects"] = TeamProjectsTable(
            Project.objects.filter(team=self.object)
        )

        return context


class TeamMembersTable(Table):
    class Meta:
        model = CustomUser
        attrs = {"class": "table"}
        fields = (
            "email",
            "last_login",
            "date_joined",
        )

    email = Column(verbose_name="Email")
    last_login = NaturalDatetimeColumn()
    date_joined = NaturalDatetimeColumn()


class TeamMembers(DetailView):
    template_name = "teams/members.html"
    model = Team

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["team_members"] = TeamMembersTable(
            self.object.members.all()
        )

        return context


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
        "teams/settings.html",
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
