from unittest.mock import MagicMock

import pytest
from django.conf import settings
from django.core import mail

from apps.base.tests.mock_data import TABLE
from apps.base.tests.mocks import mock_bq_client_with_schema
from apps.exports import tasks
from apps.exports.models import Export
from apps.nodes.models import Node

pytestmark = pytest.mark.django_db

SIGNED_URL = "https://export.save.url"

TEMPORARY_TABLE = "temporary_table"


@pytest.fixture
def mock_bigquery_functions(mocker, bigquery):
    bigquery.query = MagicMock()
    bigquery.query.return_value.destination = TEMPORARY_TABLE
    bigquery.extract_table = MagicMock()
    mock_bq_client_with_schema(
        bigquery, [(name, str(type_)) for name, type_ in TABLE.schema().items()]
    )

    bucket = MagicMock()
    bucket.blob.return_value.generate_signed_url.return_value = SIGNED_URL
    mocker.patch("apps.base.clients.get_bucket", return_value=bucket)


def test_export_to_gcs(
    bigquery,
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

    assert bigquery.extract_table.call_count == 1
    assert bigquery.extract_table.call_args.args == (
        TEMPORARY_TABLE,
        f"gs://{settings.GS_BUCKET_NAME}/{export.path}",
    )
