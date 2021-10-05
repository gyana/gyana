import analytics
from apps.base.analytics import PROJECT_CREATED_EVENT
from apps.base.turbo import TurboCreateView, TurboUpdateView
from apps.teams.mixins import TeamMixin
from django.shortcuts import redirect
from django.urls.base import reverse
from django.views.generic import DetailView
from django.views.generic.edit import DeleteView
from waffle import flag_is_active

from .forms import ProjectCreateForm, ProjectForm
from .models import Project


class ProjectCreate(TeamMixin, TurboCreateView):
    template_name = "projects/create.html"
    model = Project
    form_class = ProjectCreateForm

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["current_user"] = self.request.user
        form_kwargs["team"] = self.team
        form_kwargs["is_beta"] = flag_is_active(self.request, "beta")
        return form_kwargs

    def get_success_url(self) -> str:
        return reverse("projects:detail", args=(self.object.id,))

    def form_valid(self, form):
        redirect = super().form_valid(form)
        analytics.track(
            self.request.user.id, PROJECT_CREATED_EVENT, {"id": form.instance.id}
        )

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


class ProjectUpdate(TurboUpdateView):
    template_name = "projects/update.html"
    model = Project
    form_class = ProjectForm
    pk_url_kwarg = "project_id"

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["current_user"] = self.request.user
        form_kwargs["team"] = self.object.team
        form_kwargs["is_beta"] = flag_is_active(self.request, "beta")
        return form_kwargs

    def get_success_url(self) -> str:
        return reverse("projects:detail", args=(self.object.id,))


class ProjectDelete(DeleteView):
    template_name = "projects/delete.html"
    model = Project
    pk_url_kwarg = "project_id"

    def get_success_url(self) -> str:
        return reverse("teams:detail", args=(self.object.team.id,))
