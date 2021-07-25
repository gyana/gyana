import datetime
import os
import time
import uuid

import analytics
import coreapi
from apps.projects.mixins import ProjectMixin
from apps.tables.bigquery import get_query_from_table
from apps.tables.models import Table
from apps.tables.tables import TableTable
from apps.utils.clients import get_bucket
from apps.utils.segment_analytics import (
    INTEGRATION_CREATED_EVENT,
    NEW_INTEGRATION_START_EVENT,
)
from apps.utils.table_data import get_table
from celery.result import AsyncResult
from django.conf import settings
from django.contrib.postgres.search import TrigramSimilarity
from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.http.response import HttpResponseBadRequest, HttpResponseRedirect
from django.shortcuts import get_object_or_404
from django.urls import reverse
from django.utils.text import slugify
from django.views.generic import DetailView
from django.views.generic.base import TemplateResponseMixin, TemplateView, View
from django.views.generic.edit import DeleteView
from django_tables2 import SingleTableView
from django_tables2.config import RequestConfig
from django_tables2.views import SingleTableMixin
from rest_framework.decorators import api_view, schema
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.schemas import AutoSchema
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
from .tasks import (
    file_sync,
    poll_fivetran_historical_sync,
    send_integration_email,
    start_fivetran_integration_task,
    update_integration_fivetran_schema,
)
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


# Turbo frames


class IntegrationGrid(SingleTableMixin, TemplateView):
    template_name = "integrations/grid.html"
    paginate_by = 15

    def get_table_kwargs(self):
        return {"attrs": {"class": "table-data"}}

    def get_context_data(self, **kwargs):
        self.integration = Integration.objects.get(id=kwargs["pk"])

        table_id = self.request.GET.get("table_id")
        try:
            self.table_instance = (
                self.integration.table_set.get(pk=table_id)
                if table_id
                else self.integration.table_set.first()
            )
        except (Table.DoesNotExist, ValueError):
            self.table_instance = self.integration.table_set.first()

        context_data = super().get_context_data(**kwargs)
        context_data["table_instance"] = self.table_instance
        return context_data

    def get_table(self, **kwargs):
        query = get_query_from_table(self.table_instance)
        table = get_table(query.schema(), query, **kwargs)

        return RequestConfig(
            self.request, paginate=self.get_table_pagination(table)
        ).configure(table)


class IntegrationSync(TurboUpdateView):
    template_name = "integrations/sync.html"
    model = Integration
    fields = []

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data[
            "external_table_sync_task_id"
        ] = self.object.external_table_sync_task_id

        return context_data

    def form_valid(self, form):
        if self.object.kind == Integration.Kind.GOOGLE_SHEETS:
            self.object.start_sheets_sync()
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse("integrations:sync", args=(self.object.id,))


class IntegrationTablesList(ProjectMixin, SingleTableView):
    template_name = "tables/list.html"
    model = Integration
    table_class = TableTable
    paginate_by = 20

    def get_queryset(self) -> QuerySet:
        return Table.objects.filter(
            project=self.project, integration_id=self.kwargs["pk"]
        )


class IntegrationAuthorize(DetailView):

    model = Integration
    template_name = "integrations/authorize.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.object.fivetran_id is None:
            FivetranClient().create(self.object.service, self.object.projec.team.id)

        return context


# Endpoints


@api_view(["POST"])
@schema(
    AutoSchema(
        manual_fields=[
            coreapi.Field(
                name="filename",
                required=True,
                location="form",
            ),
        ]
    )
)
def generate_signed_url(request: Request, session_key: str):
    filename = request.data["filename"]
    filename, file_extension = os.path.splitext(filename)
    path = f"{settings.CLOUD_NAMESPACE}/integrations/{filename}-{slugify(time.time())}{file_extension}"

    blob = get_bucket().blob(path)
    # This signed URL allows the client to create a Session URI to use as upload pointer.
    # Delegating this to the client, because geographic location matters when starting a session
    # https://cloud.google.com/storage/docs/access-control/signed-urls#signing-resumable
    url = blob.generate_signed_url(
        version="v4",
        expiration=datetime.timedelta(minutes=15),
        method="RESUMABLE",
    )

    request.session[session_key] = {**request.session[session_key], "file": path}

    return Response({"url": url})


@api_view(["POST"])
def start_sync(request: Request, session_key: str):
    form_data = request.session[session_key]

    file_sync_task_id = file_sync.delay(form_data["file"], form_data["project"])

    request.session[session_key] = {
        **request.session[session_key],
        "file_sync_task_id": str(file_sync_task_id),
    }

    return (
        TurboStream("integration-validate-flow")
        .replace.template(
            "integrations/file_setup/_create_flow.html",
            {
                "instance_session_key": session_key,
                "file_input_id": "id_file",
                "stage": "validate",
                "file_sync_task_id": file_sync_task_id,
                "turbo_stream_url": reverse(
                    "integrations:upload_complete",
                    args=(session_key,),
                ),
            },
        )
        .response(request)
    )


@api_view(["GET"])
def upload_complete(request: Request, session_key: str):
    form_data = request.session[session_key]
    file_sync_task_result = AsyncResult(
        request.session[session_key]["file_sync_task_id"]
    )

    if file_sync_task_result.state == "SUCCESS":
        table_id, time_elapsed = file_sync_task_result.get()
        table = get_object_or_404(Table, pk=table_id)

        integration = CSVCreateForm(data=form_data).save()
        integration.file = form_data["file"]
        integration.created_by = request.user
        integration.last_synced = datetime.datetime.now()
        integration.save()

        table.integration = integration
        table.save()

        finalise_upload_task_id = send_integration_email.delay(
            integration.id, time_elapsed
        )

        return (
            TurboStream("integration-validate-flow")
            .replace.template(
                "integrations/file_setup/_create_flow.html",
                {
                    "instance_session_key": session_key,
                    "file_input_id": "id_file",
                    "stage": "finalise",
                    "finalise_upload_task_id": finalise_upload_task_id,
                    "redirect_url": reverse(
                        "project_integrations:detail",
                        args=(integration.project.id, integration.id),
                    ),
                },
            )
            .response(request)
        )


@api_view(["GET"])
def start_fivetran_integration(request: HttpRequest, session_key: str):
    integration_data = request.session[session_key]

    task_id = start_fivetran_integration_task.delay(integration_data["fivetran_id"])

    return (
        TurboStream("integration-setup-container")
        .replace.template(
            "integrations/fivetran_setup/_flow.html",
            {
                "connector_start_task_id": task_id,
                "redirect_url": reverse(
                    "integrations:finalise-fivetran-integration",
                    args=(session_key,),
                ),
            },
        )
        .response(request)
    )


@api_view(["GET"])
def finalise_fivetran_integration(request: HttpRequest, session_key: str):
    integration_data = request.session[session_key]
    # Create integration
    integration = FivetranForm(data=integration_data).save()
    integration.schema = integration_data["schema"]
    integration.fivetran_id = integration_data["fivetran_id"]
    integration.created_by = request.user
    # Start polling
    task_id = poll_fivetran_historical_sync.delay(integration.id)
    integration.fivetran_poll_historical_sync_task_id = str(task_id)
    integration.save()

    analytics.track(
        request.user.id,
        INTEGRATION_CREATED_EVENT,
        {
            "id": integration.id,
            "type": integration.kind,
            "name": integration.name,
        },
    )

    return HttpResponseRedirect(
        reverse(
            "project_integrations:detail",
            args=(integration.project.id, integration.id),
        )
    )
