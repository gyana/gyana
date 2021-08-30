from functools import cached_property

from apps.base.turbo import TurboCreateView
from apps.teams.mixins import TeamMixin
from django.urls.base import reverse
from django_tables2 import SingleTableView

from .forms import TemplateInstanceCreateForm
from .models import Template, TemplateInstance
from .tables import TemplateTable


class TemplateList(TeamMixin, SingleTableView):
    template_name = "templates/list.html"
    model = Template
    table_class = TemplateTable
    paginate_by = 20


class TemplateInstanceCreate(TeamMixin, TurboCreateView):
    template_name = "templates/create.html"
    model = TemplateInstance
    form_class = TemplateInstanceCreateForm

    @cached_property
    def template(self):
        return Template.objects.get(pk=self.kwargs["template_id"])

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["template"] = self.template
        return context

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["team"] = self.team
        kwargs["template"] = self.template
        return kwargs

    def get_success_url(self) -> str:
        return reverse("projects:detail", args=(self.object.project.id,))
