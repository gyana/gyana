import pytest
from apps.base.tests.asserts import assertFormRenders, assertOK
from apps.integrations.models import Integration
from apps.projects.models import Project
from pytest_django.asserts import assertRedirects

pytestmark = pytest.mark.django_db


def test_create(_, client, logged_in_user, bigquery_client):

    team = logged_in_user.teams.first()
    project = Project.objects.create(name="Project", team=team)

    # create a new connector, configure it and complete the sync

    # create
    r = client.get(f"/projects/{project.id}/integrations/connectors/new")
    assertOK(r)
    # assertFormRenders(r, ["url"])

    r = client.post(
        f"/projects/{project.id}/integrations/connectors/new",
        data={
            "url": "https://docs.google.com/spreadsheets/d/1mfauospJlft0B304j7em1vcyE1QKKVMhZjyLfIAnvmU/edit"
        },
    )

    integration = project.integration_set.first()
    assert integration is not None
    assert integration.kind == Integration.Kind.CONNECTOR
    assert integration.connector is not None
    assert integration.created_by == logged_in_user
    INTEGRATION_URL = f"/projects/{project.id}/integrations/{integration.id}"

    assertRedirects(r, f"{INTEGRATION_URL}/configure", status_code=303)

    # configure
    r = client.get(f"{INTEGRATION_URL}/configure")
    assertOK(r)
    # todo: fix this!
    assertFormRenders(r, ["name", "cell_range"])

    # mock the configuration
    bigquery_client.query().exception = lambda: False
    bigquery_client.reset_mock()  # reset the call count
    bigquery_client.get_table().num_rows = 10

    assert bigquery_client.query.call_count == 0

    # complete the sync
    # it will happen immediately as celery is run in eager mode
    r = client.post(
        f"{INTEGRATION_URL}/configure",
        data={"cell_range": "store_info!A1:D11"},
    )

    assert bigquery_client.query.call_count == 1
    assertRedirects(r, f"{INTEGRATION_URL}/load", target_status_code=302)

    r = client.get(f"{INTEGRATION_URL}/load")
    assertRedirects(r, f"{INTEGRATION_URL}/done")

    # todo: email
    # assert len(mail.outbox) == 1
