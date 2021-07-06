from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import HttpResponse
from django.urls import reverse
from django.utils.translation import ugettext_lazy as _
from django.views.generic import DeleteView, DetailView, UpdateView
from turbo_response.views import TurboCreateView

from .forms import TeamChangeForm
from .models import Team


class TeamCreate(LoginRequiredMixin, TurboCreateView):
    model = Team
    form_class = TeamChangeForm
    template_name = "teams/create.html"

    def form_valid(self, form: forms.Form) -> HttpResponse:
        form.save()
        form.instance.members.add(self.request.user, through_defaults={"role": "admin"})

        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse("teams:detail", args=(self.object.id,))


class TeamUpdate(LoginRequiredMixin, UpdateView):
    template_name = "teams/update.html"
    form_class = TeamChangeForm
    model = Team

    def get_success_url(self) -> str:
        return reverse("teams:update", args=(self.object.id,))


class TeamDelete(LoginRequiredMixin, DeleteView):
    template_name = "teams/delete.html"
    model = Team

    def get_success_url(self) -> str:
        return reverse("web:home")


class TeamDetail(DetailView):
    template_name = "teams/detail.html"
    model = Team

    def get_context_data(self, **kwargs):
        from apps.projects.models import Project

        from .tables import TeamProjectsTable

        context = super().get_context_data(**kwargs)
        context["team_projects"] = TeamProjectsTable(
            Project.objects.filter(team=self.object)
        )
        context["project_count"] = Project.objects.filter(team=self.object).count()

        return context


class TeamMembers(DetailView):
    template_name = "teams/members.html"
    model = Team

    def get_context_data(self, **kwargs):
        from .tables import TeamMembersTable

        context = super().get_context_data(**kwargs)
        context["team_members"] = TeamMembersTable(self.object.members.all())

        return context
