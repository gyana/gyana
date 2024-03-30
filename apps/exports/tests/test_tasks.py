import pytest
from django.conf import settings
from django.core import mail
from google.cloud.bigquery import Client

from apps.exports import tasks
from apps.exports.models import Export
from apps.nodes.models import Node

pytestmark = pytest.mark.django_db

SIGNED_URL = "https://export.save.url"

TEMPORARY_TABLE = "temporary_table"


@pytest.fixture
def mock_bigquery_functions(mocker):
    query = mocker.MagicMock()
    query.destination = TEMPORARY_TABLE
    mocker.patch.object(Client, "query", return_value=query)

    mocker.patch.object(Client, "extract_table")

    bucket = mocker.MagicMock()
    bucket.blob.return_value.generate_signed_url.return_value = SIGNED_URL
    mocker.patch("apps.base.clients.get_bucket", return_value=bucket)
    return mocker.patch.object(Client, "extract_table")


def test_export_to_gcs(
    mock_bigquery_functions,
    node_factory,
    logged_in_user,
    integration_table_factory,
):
    table = integration_table_factory()
    input_node = node_factory(kind=Node.Kind.INPUT, input_table=table)
    export = Export(node=input_node, created_by=logged_in_user)
    export.save()

    tasks.export_to_gcs(export.id, logged_in_user.id)

    export.refresh_from_db()

    assert export.exported_at is not None

    assert len(mail.outbox) == 1
    assert SIGNED_URL in mail.outbox[0].body

    assert mock_bigquery_functions.call_count == 1
    assert mock_bigquery_functions.call_args.args == (
        TEMPORARY_TABLE,
        f"gs://{settings.GS_BUCKET_NAME}/{export.path}",
    )
