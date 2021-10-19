from unittest.mock import patch

import pytest
from apps.base.tests.asserts import assertFormRenders, assertOK
from apps.integrations.models import Integration
from apps.projects.models import Project
from django.core import mail
from pytest_django.asserts import assertRedirects

pytestmark = pytest.mark.django_db


@patch("apps.uploads.bigquery.bq_table_schema_is_string_only", return_value=False)
def test_create(_, client, logged_in_user, bigquery_client):

    team = logged_in_user.teams.first()
    project = Project.objects.create(name="Project", team=team)

    # create a new upload, configure it and complete the sync

    # create
    r = client.get(f"/projects/{project.id}/integrations/uploads/new")
    assertOK(r)
    # the form uses React, tested in Cypress

    r = client.post(
        f"/projects/{project.id}/integrations/uploads/new",
        data={"file_name": "store_info.csv", "file_gcs_path": "path/to/gcs"},
    )

    integration = project.integration_set.first()
    assert integration is not None
    assert integration.kind == Integration.Kind.UPLOAD
    assert integration.upload is not None
    assert integration.created_by == logged_in_user
    INTEGRATION_URL = f"/projects/{project.id}/integrations/{integration.id}"

    assertRedirects(r, f"{INTEGRATION_URL}/configure", status_code=303)

    # configure
    r = client.get(f"{INTEGRATION_URL}/configure")
    assertOK(r)
    # todo: fix this!
    assertFormRenders(r, ["name", "field_delimiter"])

    # mock the configuration
    bigquery_client.load_table_from_uri().exception = lambda: False
    bigquery_client.reset_mock()  # reset the call count
    bigquery_client.get_table().num_rows = 10

    assert bigquery_client.query.call_count == 0

    # complete the sync
    # it will happen immediately as celery is run in eager mode
    r = client.post(
        f"{INTEGRATION_URL}/configure",
        data={"field_delimiter": "comma"},
    )

    assert bigquery_client.load_table_from_uri.call_count == 1
    assertRedirects(r, f"{INTEGRATION_URL}/load", target_status_code=302)

    r = client.get(f"{INTEGRATION_URL}/load")
    assertRedirects(r, f"{INTEGRATION_URL}/done")

    # todo: email
    # assert len(mail.outbox) == 1
