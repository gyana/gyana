from apps.cnames.models import CName
from apps.columns.models import (
    AddColumn,
    AggregationColumn,
    EditColumn,
    FormulaColumn,
    WindowColumn,
)
from apps.connectors.models import Connector
from apps.dashboards.models import Dashboard
from apps.filters.models import Filter
from apps.integrations.models import Integration
from apps.nodes.models import Node
from apps.projects.models import Project
from apps.sheets.models import Sheet
from apps.tables.models import Table
from apps.teams.models import Team
from apps.uploads.models import Upload
from apps.widgets.models import Widget
from apps.workflows.models import Workflow
from pytest_factoryboy import register

import factory


@register
class TeamFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Team

    name = "Team"


@register
class ProjectFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Project

    name = "Project"
    team = factory.SubFactory(TeamFactory)


@register
class IntegrationFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Integration

    project = factory.SubFactory(ProjectFactory)
    ready = True
    state = Integration.State.DONE


@register
class ConnectorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Connector

    service = "google_analytics"
    schema = "schema"
    fivetran_authorized = True
    integration = factory.SubFactory(
        IntegrationFactory, kind=Integration.Kind.CONNECTOR, name="Google Analytics"
    )


@register
class SheetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Sheet

    url = "http://sheet.url"
    cell_range = "store_info!A1:D10"
    integration = factory.SubFactory(
        IntegrationFactory, kind=Integration.Kind.SHEET, name="Store info"
    )


@register
class UploadFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Upload

    file_gcs_path = "/path/to/gcs"
    integration = factory.SubFactory(
        IntegrationFactory, kind=Integration.Kind.UPLOAD, name="Store info"
    )


@register
class IntegrationTableFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Table

    source = Table.Source.INTEGRATION
    bq_table = "table"
    bq_dataset = "dataset"
    num_rows = 10


@register
class WorkflowFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Workflow

    project = factory.SubFactory(ProjectFactory)


@register
class DashboardFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Dashboard

    project = factory.SubFactory(ProjectFactory)


@register
class WidgetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Widget


@register
class CNameFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CName

    domain = "test.domain.com"


@register
class NodeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Node

    workflow = factory.SubFactory(WorkflowFactory)
    x = 0
    y = 0


@register
class AggregationColumnFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AggregationColumn


@register
class EditColumnFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EditColumn


@register
class AddColumnFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AddColumn


@register
class FormulaColumnFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FormulaColumn


@register
class WindowColumnFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WindowColumn


@register
class FilterFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Filter
