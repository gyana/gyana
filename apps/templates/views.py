import analytics
from django.shortcuts import redirect
from django.urls.base import reverse
from django.utils.functional import cached_property
from django_tables2 import SingleTableView
from django_tables2.views import SingleTableMixin

from apps.base.analytics import (
    TEMPLATE_COMPLETED_EVENT,
    TEMPLATE_CREATED_EVENT,
    TEMPLATE_VIEWED_EVENT,
)
from apps.base.frames import TurboFrameListView
from apps.base.views import TurboCreateView, TurboUpdateView
from apps.projects.mixins import ProjectMixin
from apps.teams.mixins import TeamMixin
from apps.templates.forms import TemplateInstanceUpdateForm

from .forms import TemplateInstanceCreateExistingForm, TemplateInstanceCreateNewForm
from .models import Template, TemplateInstance
from .tables import TemplateInstanceTable, TemplateIntegrationTable, TemplateTable


class TemplateList(TeamMixin, SingleTableView, TurboFrameListView):
    template_name = "templates/list.html"
    model = Template
    table_class = TemplateTable
    paginate_by = 20
    turbo_frame_dom_id = "templates:list"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        context_data["templates"] = Template.objects.all()

        return context_data


class TemplateInstanceCreate(TeamMixin, TurboCreateView):
    template_name = "templateinstances/create.html"
    model = TemplateInstance

    def get_form_class(self):
        if self.request.POST.get("submit") == "create":
            return TemplateInstanceCreateNewForm
        return TemplateInstanceCreateExistingForm

    @cached_property
    def template(self):
        return Template.objects.get(pk=self.kwargs["template_id"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["template"] = self.template
        return context

    def get(self, request, *args, **kwargs):
        analytics.track(
            self.request.user.id, TEMPLATE_VIEWED_EVENT, {"id": self.template.id}
        )
        return super().get(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["team"] = self.team
        kwargs["template"] = self.template
        return kwargs

    def form_valid(self, form):
        redirect = super().form_valid(form)
        analytics.track(
            self.request.user.id, TEMPLATE_CREATED_EVENT, {"id": self.template.id}
        )
        return redirect

    def get_success_url(self) -> str:
        return reverse(
            "project_templateinstances:update",
            args=(self.object.project.id, self.object.id),
        )


class TemplateInstanceList(ProjectMixin, SingleTableView):
    template_name = "templateinstances/list.html"
    model = TemplateInstance
    table_class = TemplateInstanceTable
    paginate_by = 20

    def get_queryset(self):
        return self.project.templateinstance_set.all()

    def get(self, request, *args, **kwargs):
        if not self.project.ready:
            return redirect(
                "project_templateinstances:update",
                self.project.id,
                self.project.templateinstance_set.first().id,
            )
        return super().get(request, *args, **kwargs)


class TemplateInstanceUpdate(ProjectMixin, SingleTableMixin, TurboUpdateView):
    template_name = "templateinstances/update.html"
    model = TemplateInstance
    form_class = TemplateInstanceUpdateForm
    table_class = TemplateIntegrationTable

    def get_context_data(self, **kwargs):

        for template_integration in self.object.templateintegration_set.filter(
            target_integration__isnull=True
        ).all():
            target_integration = self.project.integration_set.filter(
                connector__service=template_integration.source_integration.connector.service
            ).first()

            if target_integration is not None:
                template_integration.target_integration = target_integration
                template_integration.save()

        return super().get_context_data(**kwargs)

    def get_table_kwargs(self):
        return {"show_header": False, "project": self.project}

    def get_table_data(self):
        return self.object.templateintegration_set.all()

    def form_valid(self, form):
        redirect = super().form_valid(form)
        analytics.track(
            self.request.user.id,
            TEMPLATE_COMPLETED_EVENT,
            {"id": self.object.template.id},
        )
        return redirect

    def get_success_url(self):
        return reverse("projects:detail", args=(self.project.id,))
