from django.conf import settings
from django.contrib.auth.mixins import LoginRequiredMixin
from django.db.models import Q
from django.http import HttpResponse
from django.http.response import Http404
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DeleteView, DetailView
from django.views.generic.edit import UpdateView
from django_tables2.views import SingleTableMixin, SingleTableView
from djpaddle.models import Plan

from apps.base.turbo import TurboCreateView, TurboUpdateView
from apps.teams.mixins import TeamMixin

from .forms import MembershipUpdateForm, TeamCreateForm, TeamUpdateForm
from .models import Membership, Team
from .tables import TeamMembershipTable, TeamProjectsTable


class TeamCreate(LoginRequiredMixin, TurboCreateView):
    model = Team
    form_class = TeamCreateForm
    template_name = "teams/create.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_success_url(self) -> str:
        return reverse("teams:plan", args=(self.object.id,))


class TeamPlan(LoginRequiredMixin, TurboUpdateView):
    model = Team
    form_class = TeamCreateForm
    template_name = "teams/plan.html"
    pk_url_kwarg = "team_id"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["paddle_plan"] = Plan.objects.first()
        context["djpaddle_checkout_success_redirect"] = reverse(
            "teams:account", args=(self.object.id,)
        )
        context["DJPADDLE_VENDOR_ID"] = settings.DJPADDLE_VENDOR_ID
        context["DJPADDLE_SANDBOX"] = settings.DJPADDLE_SANDBOX
        return context

    def get_success_url(self) -> str:
        return reverse("teams:detail", args=(self.object.id,))


class TeamUpdate(LoginRequiredMixin, TurboUpdateView):
    template_name = "teams/update.html"
    form_class = TeamUpdateForm
    model = Team
    pk_url_kwarg = "team_id"

    def get_success_url(self) -> str:
        return reverse("teams:update", args=(self.object.id,))


class TeamDelete(LoginRequiredMixin, DeleteView):
    template_name = "teams/delete.html"
    model = Team
    pk_url_kwarg = "team_id"

    def get_success_url(self) -> str:
        return reverse("web:home")


class TeamDetail(SingleTableMixin, DetailView):
    template_name = "teams/detail.html"
    model = Team
    pk_url_kwarg = "team_id"
    table_class = TeamProjectsTable
    paginate_by = 15

    def get_context_data(self, **kwargs):
        from apps.projects.models import Project

        self.request.session["team_id"] = self.object.id
        self.projects = Project.objects.filter(team=self.object).filter(
            Q(access=Project.Access.EVERYONE) | Q(members=self.request.user)
        )

        context = super().get_context_data(**kwargs)
        context["project_count"] = self.projects.count()

        return context

    def get_table_data(self):
        return self.projects


class TeamAccount(UpdateView):
    template_name = "teams/account.html"
    model = Team
    pk_url_kwarg = "team_id"
    fields = []

    def form_valid(self, form) -> HttpResponse:
        self.object.update_row_count()
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse("teams:account", args=(self.object.id,))


class MembershipList(TeamMixin, SingleTableView):
    template_name = "members/list.html"
    model = Membership
    table_class = TeamMembershipTable
    paginate_by = 20

    def get_queryset(self):
        return Membership.objects.filter(team=self.team).all()


class MembershipUpdate(TeamMixin, TurboUpdateView):
    template_name = "members/update.html"
    model = Membership
    form_class = MembershipUpdateForm

    def get_success_url(self) -> str:
        return reverse("team_members:list", args=(self.team.id,))


class MembershipDelete(TeamMixin, DeleteView):
    template_name = "members/delete.html"
    model = Membership

    def delete(self, request, *args, **kwargs) -> HttpResponse:
        if self.get_object().can_delete:
            return super().delete(request, *args, **kwargs)
        raise Http404("Cannot delete last admin of team")

    def get_success_url(self) -> str:
        return reverse("team_members:list", args=(self.team.id,))
