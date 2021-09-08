from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.http.response import Http404
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DeleteView, DetailView
from django.views.generic.edit import UpdateView
from django_tables2.views import SingleTableView

from apps.base.turbo import TurboCreateView, TurboUpdateView
from apps.teams.mixins import TeamMixin

from .forms import MembershipUpdateForm, TeamCreateForm, TeamUpdateForm
from .models import Membership, Team
from .tables import TeamMembershipTable


class TeamCreate(LoginRequiredMixin, TurboCreateView):
    model = Team
    form_class = TeamCreateForm
    template_name = "teams/create.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

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


class TeamDetail(DetailView):
    template_name = "teams/detail.html"
    model = Team
    pk_url_kwarg = "team_id"

    def get_context_data(self, **kwargs):
        from apps.projects.models import Project

        from .tables import TeamProjectsTable

        self.request.session["team_id"] = self.object.id

        context = super().get_context_data(**kwargs)
        context["team_projects"] = TeamProjectsTable(
            Project.objects.filter(team=self.object)
        )
        context["project_count"] = Project.objects.filter(team=self.object).count()


        return context


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
