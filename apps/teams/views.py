from django.db.models import Q
from django.http import HttpResponse
from django.http.response import Http404
from django.urls import reverse
from django.views.generic import CreateView, DeleteView, DetailView
from django_tables2.views import SingleTableMixin, SingleTableView

from apps.base.views import UpdateView

from .forms import MembershipUpdateForm, TeamCreateForm, TeamUpdateForm
from .mixins import TeamMixin
from .models import Membership, Team
from .tables import TeamMembershipTable, TeamProjectsTable


class TeamCreate(CreateView):
    model = Team
    form_class = TeamCreateForm
    template_name = "teams/create.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_success_url(self) -> str:
        return reverse("teams:detail", args=(self.object.id,))


class TeamUpdate(UpdateView):
    template_name = "teams/update.html"
    form_class = TeamUpdateForm
    model = Team
    pk_url_kwarg = "team_id"

    def get_success_url(self) -> str:
        return reverse("teams:update", args=(self.object.id,))


class TeamDelete(DeleteView):
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
        self.projects = (
            Project.objects.filter(team=self.object)
            .filter(Q(access=Project.Access.EVERYONE) | Q(members=self.request.user))
            .distinct()
        )

        context = super().get_context_data(**kwargs)
        context["project_count"] = self.projects.count()

        return context

    def get_table_data(self):
        return self.projects


class MembershipList(TeamMixin, SingleTableView):
    template_name = "members/list.html"
    model = Membership
    table_class = TeamMembershipTable
    paginate_by = 20

    def get_queryset(self):
        return Membership.objects.filter(team=self.team).all()


class MembershipUpdate(TeamMixin, UpdateView):
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
