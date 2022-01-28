import pytest

from apps.base.tests.asserts import assertLoginRedirect, assertNotFound, assertOK

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "url",
    [
        pytest.param("/connectors/{connector_id}/customreports/", id="list"),
        pytest.param("/connectors/{connector_id}/customreports/new", id="create"),
        pytest.param(
            "/connectors/{connector_id}/customreports/{customreport_id}/update",
            id="update",
        ),
        pytest.param(
            "/connectors/{connector_id}/customreports/{customreport_id}/delete",
            id="delete",
        ),
    ],
)
def test_access(client, url, user, facebook_ads_custom_report_factory):
    customreport = facebook_ads_custom_report_factory()
    connector = customreport.connector
    project = connector.integration.project
    url = url.format(connector_id=connector.id, customreport_id=customreport.id)

    assertLoginRedirect(client, url)

    client.force_login(user)
    r = client.get(url)
    assertNotFound(r)

    project.team = user.teams.first()
    project.save()
    r = client.get(url)
    assertOK(r)
