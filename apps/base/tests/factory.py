from apps.connectors.models import Connector
from apps.integrations.models import Integration
from apps.projects.models import Project
from apps.tables.models import Table
from apps.teams.models import Team
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
class IntegrationTableFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Table

    project = factory.Iterator(Project.objects.all())
    integration = factory.Iterator(Integration.objects.all())
    source = Table.Source.INTEGRATION
    bq_table = "table"
    bq_dataset = "dataset"
