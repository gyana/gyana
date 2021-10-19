from unittest.mock import MagicMock, Mock

from apps.base.clients import bigquery_client
from google.cloud.bigquery.schema import SchemaField
from google.cloud.bigquery.table import Table as BqTable


class PickableMock(Mock):
    def __reduce__(self):
        return (Mock, ())


def mock_bq_client_with_schema(bigquery_client, schema_list):
    bq_table = BqTable(
        "project.dataset.table",
        schema=[SchemaField(column, type_) for column, type_ in schema_list],
    )
    bigquery_client.get_table = MagicMock(return_value=bq_table)


def mock_bq_client_with_data(bigquery_client, records):
    mock = PickableMock()
    mock.rows_dict = records
    mock.total_rows = 2
    bigquery_client.get_query_results = Mock(return_value=mock)
