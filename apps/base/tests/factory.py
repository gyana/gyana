import uuid

import factory
from django.utils import timezone
from pytest_factoryboy import register

from apps.columns.models import (
    AddColumn,
    AggregationColumn,
    Column,
    ConvertColumn,
    EditColumn,
    FormulaColumn,
    JoinColumn,
    RenameColumn,
    WindowColumn,
)
from apps.controls.models import Control, ControlWidget
from apps.customapis.models import CustomApi
from apps.dashboards.models import Dashboard, Page
from apps.filters.models import Filter
from apps.integrations.models import Integration
from apps.invites.models import Invite
from apps.nodes.models import Node
from apps.oauth2.models import OAuth2
from apps.projects.models import Project
from apps.runs.models import GraphRun, JobRun
from apps.sheets.models import Sheet
from apps.tables.models import Table
from apps.teams.models import Flag, Team
from apps.uploads.models import Upload
from apps.widgets.models import Widget
from apps.workflows.models import Workflow


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

    kind = Integration.Kind.UPLOAD
    project = factory.SubFactory(ProjectFactory)
    ready = True
    state = Integration.State.DONE


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

    project = factory.SubFactory(ProjectFactory)
    integration = factory.SubFactory(IntegrationFactory)
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
class NodeFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Node

    workflow = factory.SubFactory(WorkflowFactory)
    x = 0
    y = 0
    kind = Node.Kind.INPUT


@register
class WorkflowTableFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Table

    project = factory.SubFactory(ProjectFactory)
    workflow_node = factory.SubFactory(NodeFactory, kind=Node.Kind.OUTPUT)
    source = Table.Source.WORKFLOW_NODE
    bq_table = "table"
    bq_dataset = "dataset"
    num_rows = 10


@register
class PageFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Page

    dashboard = factory.SubFactory(DashboardFactory)


@register
class WidgetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Widget

    page = factory.SubFactory(PageFactory)
    table = factory.SubFactory(IntegrationTableFactory)


@register
class AggregationColumnFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AggregationColumn

    node = factory.SubFactory(NodeFactory)


@register
class EditColumnFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = EditColumn

    node = factory.SubFactory(NodeFactory)


@register
class AddColumnFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = AddColumn

    node = factory.SubFactory(NodeFactory)


@register
class FormulaColumnFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = FormulaColumn

    node = factory.SubFactory(NodeFactory)


@register
class JoinColumnFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = JoinColumn

    node = factory.SubFactory(NodeFactory)


@register
class RenameColumnFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = RenameColumn

    node = factory.SubFactory(NodeFactory)


@register
class WindowColumnFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = WindowColumn

    node = factory.SubFactory(NodeFactory)


@register
class FilterFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Filter


@register
class ConvertColumnFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ConvertColumn

    node = factory.SubFactory(NodeFactory)


@register
class ControlFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Control

    page = factory.SubFactory(PageFactory)


@register
class ControlWidgetFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = ControlWidget

    control = factory.SubFactory(ControlFactory)
    page = factory.SubFactory(PageFactory)


@register
class JobRunFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = JobRun


@register
class GraphRunFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = GraphRun


@register
class CustomApiFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = CustomApi


@register
class OAuth2Factory(factory.django.DjangoModelFactory):
    class Meta:
        model = OAuth2


@register
class InviteFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Invite

    sent = timezone.now()


@register
class ColumnFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Column


@register
class FlagFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Flag