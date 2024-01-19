import hashlib
from unittest.mock import MagicMock, Mock

import pyarrow as pa
from google.cloud.bigquery.schema import SchemaField
from google.cloud.bigquery.table import Table as BqTable

from apps.base.tests.fixtures import bind


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


def mock_bq_client_with_records(bigquery, records, return_count=False):
    def mock_query(stmt, *args, **kwargs):
        r = MagicMock()
        if "`count`" in stmt:
            r.to_arrow = MagicMock(
                return_value=pa.Table.from_pydict(
                    {"count": [len(list(records.values())[0])]}
                )
            )
            r.total_rows = 1
        else:
            r.to_arrow = MagicMock(return_value=pa.Table.from_pydict(records))
            r.total_rows = len(records)
        return r

    bigquery.query_and_wait.side_effect = mock_query
