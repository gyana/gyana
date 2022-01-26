import analytics
from django.shortcuts import redirect
from django.urls.base import reverse
from django.views.generic import DetailView
from django.views.generic.edit import DeleteView

from apps.base.analytics import PROJECT_CREATED_EVENT
from apps.base.views import TurboCreateView, TurboUpdateView
from apps.teams.mixins import TeamMixin

from .forms import ProjectCreateForm, ProjectUpdateForm
from .models import Project


class ProjectTeamMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["team"] = self.object.team
        return context


class ProjectCreate(TeamMixin, TurboCreateView):
    template_name = "projects/create.html"
    model = Project
    form_class = ProjectCreateForm

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["current_user"] = self.request.user
        form_kwargs["team"] = self.team
        return form_kwargs

    def get_success_url(self) -> str:
        return reverse("projects:detail", args=(self.object.id,))

    def form_valid(self, form):
        redirect = super().form_valid(form)
        analytics.track(
            self.request.user.id, PROJECT_CREATED_EVENT, {"id": form.instance.id}
        )

        return redirect


class ProjectDetail(ProjectTeamMixin, DetailView):
    template_name = "projects/detail.html"
    model = Project
    pk_url_kwarg = "project_id"

    def get(self, request, *args, **kwargs):
        object = self.get_object()

        if not object.ready:
            return redirect("project_templateinstances:list", object.id)

        return super().get(request, *args, **kwargs)


class ProjectUpdate(ProjectTeamMixin, TurboUpdateView):
    template_name = "projects/update.html"
    model = Project
    form_class = ProjectUpdateForm
    pk_url_kwarg = "project_id"

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["current_user"] = self.request.user
        form_kwargs["team"] = self.object.team
        return form_kwargs

    def get_success_url(self) -> str:
        return reverse("projects:update", args=(self.object.id,))


class ProjectDelete(ProjectTeamMixin, DeleteView):
    template_name = "projects/delete.html"
    model = Project
    pk_url_kwarg = "project_id"

    def get_success_url(self) -> str:
        return reverse("teams:detail", args=(self.object.team.id,))


class ProjectAutomate(ProjectTeamMixin, DetailView):
    template_name = "projects/automate.html"
    model = Project
    pk_url_kwarg = "project_id"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.object.update_schedule()
        return context

    def get_success_url(self):
        return reverse("projects:automate", args=(self.object.id,))


class ProjectDuplicate(ProjectTeamMixin, TurboUpdateView):
    model = Project
    fields = []
    extra_context = {"object_name": "project"}
    pk_url_kwarg = "project_id"

    def form_valid(self, form):
        from apps.nodes.models import Node
        from apps.tables.models import Table

        self.clone = self.object.make_clone({"name": "Copy " + self.object.name})

        tables = Table.objects.filter(project=self.clone).all()
        input_nodes = Node.objects.filter(
            workflow__project=self.clone,
            kind=Node.Kind.INPUT,
            input_table__isnull=False,
        ).all()

        for node in input_nodes:
            node.input_table = next(
                filter(lambda t: t.copied_from == node.input_table.id, tables)
            )
        Node.objects.bulk_update(input_nodes, ["input_table"])

        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse("projects:detail", args=(self.clone.id,))
