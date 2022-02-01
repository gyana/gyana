import pytest
from django.db import transaction

from apps.connectors.models import Connector

pytestmark = pytest.mark.django_db(transaction=True)


def test_connector_clone(connector_factory, fivetran):
    connector = connector_factory()
    clone = connector.make_clone()

    assert Connector.objects.count() == 2
    assert clone.schema != connector.schema
    assert clone.schema.startswith(
        f"team_{connector.integration.project.team.id:06}_{clone.service}_"
    )

    assert fivetran.create.call_count == 1
