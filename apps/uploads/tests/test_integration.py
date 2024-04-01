from unittest.mock import MagicMock

import pytest
from django.core import mail
from django.core.files.uploadedfile import SimpleUploadedFile
from django_drf_filepond.models import TemporaryUpload
from pytest_django.asserts import assertRedirects

from apps.base.tests.asserts import assertOK
from apps.integrations.models import Integration

pytestmark = pytest.mark.django_db


@pytest.fixture(autouse=True)
def bq_table_schema_is_not_string_only(mocker):
    mocker.patch(
        "apps.base.engine.bigquery.bq_table_schema_is_string_only", return_value=False
    )


def test_upload_create(client, logged_in_user, project, engine, mocker):

    # test: create a new upload, configure it and complete the sync

    # create
    r = client.get(f"/projects/{project.id}/integrations/uploads/new")
    assertOK(r)

    mocker.patch(
        "django_drf_filepond.models.TemporaryUpload.objects.get",
        return_value=MagicMock(file=SimpleUploadedFile("file.csv", b"")),
    )

    r = client.post(
        f"/projects/{project.id}/integrations/uploads/new",
        data={"filepond": "upload_id"},
    )

    integration = project.integration_set.first()
    assert integration is not None
    assert integration.kind == Integration.Kind.UPLOAD
    assert integration.upload is not None
    assert integration.created_by == logged_in_user
    assert engine.raw_sql.call_count == 0

    DETAIL = f"/projects/{project.id}/integrations/{integration.id}"
    assertRedirects(r, f"{DETAIL}/load", status_code=303, target_status_code=302)

    # complete the sync
    # it will happen immediately as celery is run in eager mode

    assert engine.load_table_from_uri.call_count == 1

    # validate the sql and external table configuration
    table = integration.table_set.first()
    assert engine.load_table_from_uri.call_args.args == (
        f"gs://gyana-test/{integration.upload.file}",
        table.fqn,
    )
    job_config = engine.load_table_from_uri.call_args.kwargs["job_config"]
    assert job_config.source_format == "CSV"
    assert job_config.write_disposition == "WRITE_TRUNCATE"
    assert job_config.field_delimiter == ","
    assert job_config.allow_quoted_newlines
    assert job_config.allow_jagged_rows
    assert job_config.autodetect
    assert job_config.skip_leading_rows == 1

    r = client.get(f"{DETAIL}/load")
    assertRedirects(r, f"{DETAIL}/done")

    assert len(mail.outbox) == 1
