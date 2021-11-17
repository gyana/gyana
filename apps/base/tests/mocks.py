import hashlib
from unittest.mock import MagicMock, Mock

from google.cloud.bigquery.schema import SchemaField
from google.cloud.bigquery.table import Table as BqTable


def md5(content):
    return hashlib.md5(content.encode("utf-8")).hexdigest()


class PickableMock(Mock):
    def __reduce__(self):
        return (Mock, ())


TABLE_NAME = "project.dataset.table"


def mock_bq_client_with_schema(bigquery, schema_list):
    bq_table = BqTable(
        TABLE_NAME,
        schema=[SchemaField(column, type_) for column, type_ in schema_list],
    )
    bigquery.get_table = MagicMock(return_value=bq_table)


def mock_bq_client_with_records(bigquery, records):
    mock = PickableMock()
    mock.rows_dict = records
    mock.rows_dict_by_md5 = [{md5(k): v for k, v in row.items()} for row in records]
    mock.total_rows = len(records)
    bigquery.get_query_results = Mock(return_value=mock)
