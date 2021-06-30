import datetime
import json
import os
import time

import analytics
import coreapi
from apps.projects.mixins import ProjectMixin
from apps.utils.segment_analytics import (
    INTEGRATION_CREATED_EVENT,
    NEW_INTEGRATION_START_EVENT,
)
from apps.utils.table_data import get_table
from django.conf import settings
from django.db.models.query import QuerySet
from django.http import HttpRequest
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.utils.text import slugify
from django.views.generic import DetailView
from django.views.generic.base import TemplateView
from django.views.generic.edit import DeleteView
from django_tables2 import Column, SingleTableView, Table
from django_tables2.config import RequestConfig
from django_tables2.views import SingleTableMixin
from lib.clients import get_bucket
from rest_framework.decorators import api_view, schema
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.schemas import AutoSchema
from turbo_response.stream import TurboStream
from turbo_response.views import TurboCreateView, TurboUpdateView

from .bigquery import query_integration
from .fivetran import FivetranClient, get_services, get_service_categories
from .forms import (
    FORM_CLASS_MAP,
    CSVCreateForm,
    CSVForm,
    FivetranForm,
    GoogleSheetsForm,
    IntegrationForm
)
from .models import Integration
from .tables import IntegrationTable, StructureTable
from .tasks import poll_fivetran_historical_sync

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

        return context_data

    def get_queryset(self) -> QuerySet:
        return (
            Integration.objects.filter(project=self.project)
            .prefetch_related("table_set")
            .all()
        )

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
            self.request.user.id, NEW_INTEGRATION_START_EVENT, {"type": Integration.Kind.CSV}
        )

        return CSVCreateForm

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        response = super().form_valid(form)

        analytics.track(
            self.request.user.id,
            INTEGRATION_CREATED_EVENT,
            {
                "id": form.instance.id,
                "type": form.instance.kind,
                "name": form.instance.name,
            },
        )

        return (
            TurboStream("create-container")
            .append.template(
                "integrations/_file_upload.html",
                {
                    "integration": form.instance,
                    "file_input_id": "id_file",
                    "redirect": self.get_success_url(),
                },
            )
            .response(self.request)
        )

    def get_success_url(self) -> str:
        return reverse(
            "project_integrations:detail", args=(self.project.id, self.object.id)
        )

class IntegrationCreate(ProjectMixin, TurboCreateView):
    template_name = "integrations/create.html"
    model = Integration

    def get_context_data(self, **kwargs):
        context_data = super().get_context_data(**kwargs)
        context_data["integration_kind"] = Integration.Kind
        context_data["service_account"] = settings.GCP_BQ_SVC_ACCOUNT
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
        response = super().form_valid(form)

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
            client = FivetranClient(form.instance)
            client.create()
            internal_redirect = reverse(
                "integrations:authorize-fivetran-redirect", args=(form.instance.id,)
            )
            redirect = client.authorize(f"{settings.EXTERNAL_URL}{internal_redirect}")
            return redirect

        if form.instance.kind == Integration.Kind.GOOGLE_SHEETS:
            form.instance.start_sync()

        return response

    def get_success_url(self) -> str:
        return reverse(
            "project_integrations:detail", args=(self.project.id, self.object.id)
        )


class UsedInTable(Table):
    class Meta:
        model = Integration
        attrs = {"class": "table"}
        fields = (
            "name",
            "kind",
            "created",
            "updated",
        )

    name = Column(linkify=True)


class IntegrationDetail(ProjectMixin, TurboUpdateView):
    template_name = "integrations/detail.html"
    model = Integration
    form_class = IntegrationForm

    def get_context_data(self, **kwargs):
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

    def get_context_data(self, **kwargs):
        self.integration = Integration.objects.get(id=kwargs["pk"])
        return super().get_context_data(**kwargs)

    def get_table(self, **kwargs):
        query = query_integration(self.integration)
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
        self.object.start_sync()
        return super().form_valid(form)

    def get_success_url(self) -> str:
        return reverse("integrations:sync", args=(self.object.id,))


# Turbo frames


class IntegrationAuthorize(DetailView):

    model = Integration
    template_name = "integrations/authorize.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        integration = context["integration"]

        if integration.fivetran_id is None:
            FivetranClient(integration).create()

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
def generate_signed_url(request: Request, pk: int):
    integration = get_object_or_404(request.user.integration_set, pk=pk)

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

    integration.file = path
    integration.save()

    return Response({"url": url})


@api_view(["POST"])
def start_sync(request: Request, pk: int):
    integration = get_object_or_404(request.user.integration_set, pk=pk)
    integration.start_sync()

    return Response({})


def authorize_fivetran(request: HttpRequest, pk: int):

    integration = get_object_or_404(Integration, pk=pk)
    uri = reverse("integrations:authorize-fivetran-redirect", args=(pk,))
    redirect_uri = (
        f"{settings.EXTERNAL_URL}{uri}?original_uri={request.GET.get('original_uri')}"
    )

    return FivetranClient(integration).authorize(redirect_uri)


def authorize_fivetran_redirect(request: HttpRequest, pk: int):

    integration = get_object_or_404(Integration, pk=pk)
    integration.fivetran_authorized = True

    result = poll_fivetran_historical_sync.delay(integration.id)
    integration.fivetran_poll_historical_sync_task_id = result.task_id

    integration.save()

    return redirect(
        reverse(
            "project_integrations:detail", args=(integration.project.id, integration.id)
        )
    )
