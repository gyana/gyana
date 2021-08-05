import uuid

import analytics
from apps.projects.mixins import ProjectMixin
from apps.base.segment_analytics import (
    INTEGRATION_CREATED_EVENT,
    NEW_INTEGRATION_START_EVENT,
)
from django.conf import settings
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models.query import QuerySet
from django.http.response import HttpResponseBadRequest
from django.urls import reverse
from django.views.generic import DetailView
from django.views.generic.base import TemplateResponseMixin, TemplateView, View
from django.views.generic.edit import DeleteView
from django_tables2 import SingleTableView
from turbo_response.stream import TurboStream
from turbo_response.views import TurboCreateView, TurboUpdateView

from .fivetran import FivetranClient
from .forms import (
    FORM_CLASS_MAP,
    CSVCreateForm,
    FivetranForm,
    GoogleSheetsForm,
    IntegrationForm,
)
from .models import Integration
from .tables import IntegrationTable, StructureTable
from .tasks import update_integration_fivetran_schema
from .utils import get_service_categories, get_services

# CRUDL


class IntegrationList(ProjectMixin, SingleTableView):
    template_name = "integrations/list.html"
    model = Integration
    table_class = IntegrationTable
    paginate_by = 20

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        context_data["integration_count"] = Integration.objects.filter(
            project=self.project
        ).count()

        context_data["integration_kinds"] = Integration.Kind.choices

        return context_data

    def get_queryset(self) -> QuerySet:
        queryset = Integration.objects.filter(project=self.project)
        # Add search query if it exists
        if query := self.request.GET.get("q"):
            queryset = (
                queryset.annotate(
                    similarity=TrigramSimilarity("name", query),
                )
                .filter(similarity__gt=0.05)
                .order_by("-similarity")
            )
        if (kind := self.request.GET.get("kind")) and kind in Integration.Kind.values:
            queryset = queryset.filter(kind=kind)

        return queryset.prefetch_related("table_set").all()


class IntegrationUpload(ProjectMixin, TurboCreateView):
    template_name = "integrations/upload.html"
    model = Integration

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["integration_kind"] = Integration.Kind.CSV

        return context_data

    def get_initial(self):
        initial = super().get_initial()
        initial["kind"] = Integration.Kind.CSV
        initial["project"] = self.project

        return initial

    def get_form_class(self):
        analytics.track(
            self.request.user.id,
            NEW_INTEGRATION_START_EVENT,
            {"type": Integration.Kind.CSV},
        )

        return CSVCreateForm

    def form_valid(self, form):
        instance_session_key = uuid.uuid4().hex

        if not form.is_valid():
            return HttpResponseBadRequest()

        self.request.session[instance_session_key] = {
            **form.cleaned_data,
            "project": form.cleaned_data["project"].id,
        }

        return (
            TurboStream("create-container")
            .append.template(
                "integrations/file_setup/_create_flow.html",
                {
                    "instance_session_key": instance_session_key,
                    "file_input_id": "id_file",
                    "stage": "upload",
                },
            )
            .response(self.request)
        )

    def get_success_url(self) -> str:
        return reverse(
            "project_integrations:detail", args=(self.project.id, self.object.id)
        )


class IntegrationNew(ProjectMixin, TemplateView):
    template_name = "integrations/new.html"

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["integration_kind"] = Integration.Kind
        context_data["services"] = get_services()
        context_data["service_categories"] = get_service_categories()

        return context_data


class IntegrationCreate(ProjectMixin, TurboCreateView):
    template_name = "integrations/create.html"
    model = Integration

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["integration_kind"] = Integration.Kind
        context_data["services"] = get_services()
        context_data["service_categories"] = get_service_categories()
        context_data["service_account"] = settings.GCP_BQ_SVC_ACCOUNT

        return context_data

    def get_initial(self):
        initial = super().get_initial()
        initial["kind"] = self.request.GET.get("kind")
        initial["service"] = self.request.GET.get("service")
        initial["project"] = self.project

        return initial

    def get_form_class(self):
        if (kind := self.request.GET.get("kind")) is not None:
            analytics.track(
                self.request.user.id, NEW_INTEGRATION_START_EVENT, {"type": kind}
            )

            if kind == Integration.Kind.GOOGLE_SHEETS:
                return GoogleSheetsForm
            elif kind == Integration.Kind.FIVETRAN:
                return FivetranForm

        return GoogleSheetsForm

    def form_valid(self, form):
        form.instance.created_by = self.request.user

        if form.is_valid():
            instance_session_key = uuid.uuid4().hex

            analytics.track(
                self.request.user.id,
                INTEGRATION_CREATED_EVENT,
                {
                    "id": form.instance.id,
                    "type": form.instance.kind,
                    "name": form.instance.name,
                },
            )

            if form.instance.kind == Integration.Kind.FIVETRAN:
                client = FivetranClient()
                fivetran_config = client.create(
                    form.cleaned_data["service"], form.instance.project.team.id
                )

                self.request.session[instance_session_key] = {
                    **form.cleaned_data,
                    **fivetran_config,
                    "project": form.cleaned_data["project"].id,
                    "team_id": form.instance.project.team.id,
                    "fivetran_authorized": True,
                }

                internal_redirect = reverse(
                    "project_integrations:setup",
                    args=(form.instance.project.id, instance_session_key),
                )

                return client.authorize(
                    fivetran_config["fivetran_id"],
                    f"{settings.EXTERNAL_URL}{internal_redirect}",
                )

            if form.instance.kind == Integration.Kind.GOOGLE_SHEETS:
                response = super().form_valid(form)
                form.instance.start_sheets_sync()
                return response

        return HttpResponseBadRequest()

    def get_success_url(self) -> str:
        return reverse(
            "project_integrations:detail", args=(self.project.id, self.object.id)
        )


class IntegrationDetail(ProjectMixin, TurboUpdateView):
    template_name = "integrations/detail.html"
    model = Integration
    form_class = IntegrationForm

    def get_context_data(self, **kwargs):
        from .tables import UsedInTable

        context = super().get_context_data(**kwargs)
        context["table"] = UsedInTable(self.object.used_in)

        return context

    def get_success_url(self) -> str:
        return reverse(
            "project_integrations:detail", args=(self.project.id, self.object.id)
        )


class IntegrationUpdate(ProjectMixin, TurboUpdateView):
    template_name = "integrations/update.html"
    model = Integration

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["integration_kind"] = Integration.Kind
        context_data["service_account"] = settings.GCP_BQ_SVC_ACCOUNT

        return context_data

    def get_form_class(self):
        return FORM_CLASS_MAP[self.object.kind]

    def get_success_url(self) -> str:
        return reverse(
            "project_integrations:settings", args=(self.project.id, self.object.id)
        )


class IntegrationDelete(ProjectMixin, DeleteView):
    template_name = "integrations/delete.html"
    model = Integration

    def get_success_url(self) -> str:
        return reverse("project_integrations:list", args=(self.project.id,))


class IntegrationStructure(ProjectMixin, DetailView):
    template_name = "integrations/structure.html"
    model = Integration
    table_class = StructureTable

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["tables"] = []

        for table in self.object.table_set.all():
            table_data = [
                {"type": str(field_type), "name": field_name}
                for field_name, field_type in table.schema.items()
            ]
            context_data["tables"].append(
                {"title": table.bq_table, "table_struct": StructureTable(table_data)}
            )

        return context_data


class IntegrationData(ProjectMixin, DetailView):
    template_name = "integrations/data.html"
    model = Integration

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["tables"] = self.object.table_set.all()

        return context_data


class IntegrationSchema(ProjectMixin, DetailView):
    template_name = "integrations/schema.html"
    model = Integration

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)

        context_data["integration"] = self.get_object()
        context_data["schemas"] = FivetranClient().get_schema(self.object.fivetran_id)

        return context_data

    def post(self, request, *args, **kwargs):
        integration = self.get_object()
        client = FivetranClient()
        client.update_schema(
            integration.fivetran_id,
            [key for key in request.POST.keys() if key != "csrfmiddlewaretoken"],
        )

        return TurboStream(f"{integration.id}-schema-update-message").replace.response(
            f"""<p id="{ integration.id }-schema-update-message" class="ml-4 text-green">Successfully updated the schema</p>""",
            is_safe=True,
        )


class ConnectorSetup(ProjectMixin, TemplateResponseMixin, View):
    template_name = "integrations/setup.html"

    def get_context_data(self, project_id, session_key, **kwargs):
        integration_data = self.request.session[session_key]
        return {
            "service": integration_data["service"],
            "schemas": FivetranClient().get_schema(integration_data["fivetran_id"]),
            "project": self.project,
        }

    def get(self, *args, **kwargs):
        context = self.get_context_data(**kwargs)
        return self.render_to_response(context)

    def post(self, request, session_key, **kwargs):
        integration_data = self.request.session[session_key]
        task_id = update_integration_fivetran_schema.delay(
            integration_data["fivetran_id"],
            [key for key in request.POST.keys() if key != "csrfmiddlewaretoken"],
        )

        return (
            TurboStream("integration-setup-container")
            .replace.template(
                "integrations/fivetran_setup/_flow.html",
                {
                    "table_select_task_id": task_id,
                    "turbo_url": reverse(
                        "integrations:start-fivetran-integration",
                        args=(session_key,),
                    ),
                },
            )
            .response(request)
        )


class IntegrationSettings(ProjectMixin, TurboUpdateView):
    template_name = "integrations/settings.html"
    model = Integration

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["integration_kind"] = Integration.Kind
        context_data["service_account"] = settings.GCP_BQ_SVC_ACCOUNT

        return context_data

    def get_form_class(self):
        return FORM_CLASS_MAP[self.object.kind]

    def get_success_url(self) -> str:
        return reverse(
            "project_integrations:settings", args=(self.project.id, self.object.id)
        )
