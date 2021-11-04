from unittest.mock import patch

import pytest
from apps.base.tests.asserts import assertFormRenders, assertOK
from apps.integrations.models import Integration
from apps.uploads.models import Upload
from django.core import mail
from google.cloud.bigquery import job
from pytest_django.asserts import assertRedirects

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def bq_table_schema_is_not_string_only(mocker):
    mocker.patch(
        "apps.uploads.bigquery.bq_table_schema_is_string_only", return_value=False
    )


def test_upload_create(client, logged_in_user, project_factory, bigquery):

    team = logged_in_user.teams.first()
    project = project_factory(team=team)
    # mock the configuration
    bigquery.load_table_from_uri().exception = lambda: False
    bigquery.reset_mock()  # reset the call count

    GCS_URL = "path/to/gcs"
    FIELD_DELIMITER = Upload.FieldDelimiter.COMMA

    # test: create a new upload, configure it and complete the sync

    # create
    r = client.get(f"/projects/{project.id}/integrations/uploads/new")
    assertOK(r)

    # the form uses React, tested in Cypress
    # pretend the file is upload and validate in mocked bigquery client
    r = client.post(
        f"/projects/{project.id}/integrations/uploads/new",
        data={"file_name": "store_info.csv", "file_gcs_path": GCS_URL},
    )

    integration = project.integration_set.first()
    assert integration is not None
    assert integration.kind == Integration.Kind.UPLOAD
    assert integration.upload is not None
    assert integration.created_by == logged_in_user
    DETAIL = f"/projects/{project.id}/integrations/{integration.id}"

    assertRedirects(r, f"{DETAIL}/configure", status_code=303)

    # configure
    r = client.get(f"{DETAIL}/configure")
    assertOK(r)
    # todo: fix this!
    assertFormRenders(r, ["name", "field_delimiter"])

    assert bigquery.query.call_count == 0

    # complete the sync
    # it will happen immediately as celery is run in eager mode
    r = client.post(
        f"{DETAIL}/configure",
        data={"field_delimiter": FIELD_DELIMITER},
    )

    assert bigquery.load_table_from_uri.call_count == 1

    # validate the sql and external table configuration
    table = integration.table_set.first()
    assert bigquery.load_table_from_uri.call_args.args == (
        f"gs://gyana-test/{GCS_URL}",
        table.bq_id,
    )
    job_config = bigquery.load_table_from_uri.call_args.kwargs["job_config"]
    assert job_config.source_format == "CSV"
    assert job_config.write_disposition == "WRITE_TRUNCATE"
    assert job_config.field_delimiter == ","
    assert job_config.allow_quoted_newlines
    assert job_config.allow_jagged_rows
    assert job_config.autodetect
    assert job_config.skip_leading_rows == 1

    assertRedirects(r, f"{DETAIL}/load", target_status_code=302)

    r = client.get(f"{DETAIL}/load")
    assertRedirects(r, f"{DETAIL}/done")

    # todo: email
    # assert len(mail.outbox) == 1
