from graphlib import CycleError

import analytics
import celery
from django.shortcuts import redirect
from django.urls.base import reverse
from django.utils import timezone
from django.views.generic import DetailView
from django.views.generic.edit import DeleteView

from apps.base.analytics import PROJECT_CREATED_EVENT
from apps.base.turbo import TurboCreateView, TurboUpdateView
from apps.teams.mixins import TeamMixin

from .forms import ProjectCreateForm, ProjectUpdateForm
from .models import Project


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
    form_class = ProjectUpdateForm
    pk_url_kwarg = "project_id"

    def get_form_kwargs(self):
        form_kwargs = super().get_form_kwargs()
        form_kwargs["current_user"] = self.request.user
        form_kwargs["team"] = self.object.team
        return form_kwargs

    def get_success_url(self) -> str:
        return reverse("projects:update", args=(self.object.id,))


class ProjectDelete(DeleteView):
    template_name = "projects/delete.html"
    model = Project
    pk_url_kwarg = "project_id"

    def get_success_url(self) -> str:
        return reverse("teams:detail", args=(self.object.team.id,))


class ProjectAutomate(TurboUpdateView):
    template_name = "projects/automate.html"
    model = Project
    fields = []
    pk_url_kwarg = "project_id"

    def form_valid(self, form):

        if self.request.POST.get("submit") == "cancel":
            result = celery.result.AsyncResult(str(self.object.run_task_id))
            result.revoke(terminate=True)
            self.object.cancelled_at = timezone.now()
            self.object.save()

        else:
            try:
                result = run_schedule.delay(self.object.id, trigger=True)
                self.object.run_task_id = result.task_id
                self.object.run_started_at = timezone.now()
                self.object.save()
            except CycleError:
                # todo: add an error to the schedule to track "is_circular"
                pass
        return super().form_valid(form)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        self.object.update_schedule()
        return context

    def get_success_url(self):
        return reverse("projects:automate", args=(self.object.id,))
