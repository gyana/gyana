import analytics
from apps.base.analytics import PROJECT_CREATED_EVENT
from apps.base.turbo import TurboCreateView, TurboUpdateView
from apps.projects.tables import ProjectMembershipTable
from apps.teams.mixins import TeamMixin
from django.shortcuts import get_object_or_404, redirect
from django.urls.base import reverse
from django.views.decorators.http import require_POST
from django.views.generic import DetailView
from django.views.generic.edit import DeleteView
from django_tables2.views import SingleTableMixin

from .forms import ProjectForm
from .models import Project, ProjectMembership


class ProjectCreate(TeamMixin, TurboCreateView):
    template_name = "projects/create.html"
    model = Project
    form_class = ProjectForm

    def get_initial(self):
        initial = super().get_initial()
        initial["team"] = self.team
        return initial

    def get_success_url(self) -> str:
        return reverse("projects:detail", args=(self.object.id,))

    def form_valid(self, form):
        redirect = super().form_valid(form)
        analytics.track(
            self.request.user.id, PROJECT_CREATED_EVENT, {"id": form.instance.id}
        )

        # Add creating user to project members
        if self.object.access == Project.Access.INVITE_ONLY:
            ProjectMembership(project=self.object, user=self.request.user).save()

        return redirect


class ProjectDetail(DetailView):
    template_name = "projects/detail.html"
    model = Project
    pk_url_kwarg = "project_id"

    def get(self, request, *args, **kwargs):
        object = self.get_object()

        if not object.ready:
            return redirect("project_templateinstances:list", object.id)

        return super().get(request, *args, **kwargs)


class ProjectUpdate(SingleTableMixin, TurboUpdateView):
    template_name = "projects/update.html"
    model = Project
    form_class = ProjectForm
    table_class = ProjectMembershipTable
    pk_url_kwarg = "project_id"
    paginate_by = 20

    def get_success_url(self) -> str:
        return reverse("projects:detail", args=(self.object.id,))

    def get_table_data(self):
        return self.object.projectmembership_set.all()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        project_members = [m.user for m in self.object.projectmembership_set.iterator()]
        context["team_members"] = [
            (m.user, m.user in project_members)
            for m in self.object.team.membership_set.iterator()
        ]
        return context

    def form_valid(self, form):
        redirect = super().form_valid(form)

        # Add creating user to project members
        if (
            self.object.access == Project.Access.INVITE_ONLY
            and self.request.user
            not in [m.user for m in self.object.projectmembership_set.all()]
        ):
            ProjectMembership(project=self.object, user=self.request.user).save()

        return redirect


class ProjectDelete(DeleteView):
    template_name = "projects/delete.html"
    model = Project
    pk_url_kwarg = "project_id"

    def get_success_url(self) -> str:
        return reverse("teams:detail", args=(self.object.team.id,))


@require_POST
def update_project_membership(request, project_id):
    project = get_object_or_404(Project, pk=project_id)
    selected_users = [
        m.user
        for m in project.team.membership_set.all()
        if str(m.user.id) in request.POST
    ]
    # Delete members that aren't selected anymore
    project.projectmembership_set.exclude(user__in=selected_users).delete()

    existing_members = [m.user for m in project.projectmembership_set.all()]

    ProjectMembership.objects.bulk_create(
        [
            ProjectMembership(project=project, user=user)
            for user in selected_users
            if user not in existing_members
        ]
    )
    return redirect("projects:update", project.id)
