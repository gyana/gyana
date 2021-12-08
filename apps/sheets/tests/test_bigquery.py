from unittest.mock import Mock

import pytest
from google.cloud.bigquery.schema import SchemaField

from apps.sheets.bigquery import import_table_from_sheet

pytestmark = pytest.mark.django_db


@pytest.fixture
def mock_bigquery(bigquery):
    bigquery.query().exception = lambda: False
    # the initial query
    bigquery.query().schema = [
        SchemaField("string_field_0", "STRING"),
        SchemaField("string_field_1", "STRING"),
    ]
    # result from except distinct on temporary table
    result_mock = Mock()
    result_mock.values.return_value = ["Name", "Age"]
    bigquery.query().result.return_value = [result_mock]
    bigquery.reset_mock()


def test_sheet_all_string(
    project, mock_bigquery, bigquery, sheet_factory, integration_table_factory
):

    sheet = sheet_factory(integration__project=project)
    table = integration_table_factory(project=project, integration=sheet.integration)

    import_table_from_sheet(table, sheet)

    # initial call has result with strings
    initial_call = bigquery.query.call_args_list[0]
    INTIAL_SQL = "CREATE OR REPLACE TABLE dataset.table AS SELECT * FROM table_external"
    assert initial_call.args == (INTIAL_SQL,)
    job_config = initial_call.kwargs["job_config"]
    external_config = job_config.table_definitions["table_external"]
    assert external_config.source_uris == [sheet.url]
    assert external_config.autodetect
    assert external_config.options.range == sheet.cell_range

    # header call is to a temporary table with skipped leading rows
    header_call = bigquery.query.call_args_list[1]
    HEADER_SQL = "select * from (select * from dataset.table except distinct select * from table_temp) limit 1"
    assert header_call.args == (HEADER_SQL,)
    job_config = header_call.kwargs["job_config"]
    external_config = job_config.table_definitions["table_temp"]
    assert external_config.source_uris == [sheet.url]
    assert external_config.autodetect
    assert external_config.options.range == sheet.cell_range
    assert external_config.options.skip_leading_rows == 1

    # final call with explicit schema
    final_call = bigquery.query.call_args_list[2]
    FINAL_SQL = "CREATE OR REPLACE TABLE dataset.table AS SELECT * FROM table_external"
    assert final_call.args == (FINAL_SQL,)
    job_config = final_call.kwargs["job_config"]
    external_config = job_config.table_definitions["table_external"]
    assert external_config.source_uris == [sheet.url]
    assert not external_config.autodetect
    assert external_config.options.range == sheet.cell_range
    assert external_config.options.skip_leading_rows == 1
    schema = external_config.schema
    assert schema is not None
    assert len(schema) == 2
    assert schema[0].name == "Name"
    assert schema[0].field_type == "STRING"


def get_cell_range_from_job(bigquery):
    return (
        bigquery.query.call_args_list[0]
        .kwargs["job_config"]
        .table_definitions["table_external"]
        .options.range
    )


def test_cell_range_construction(
    project, mock_bigquery, bigquery, sheet_factory, integration_table_factory
):

    sheet = sheet_factory(integration__project=project, cell_range=None)
    table = integration_table_factory(project=project, integration=sheet.integration)

    import_table_from_sheet(table, sheet)
    assert get_cell_range_from_job(bigquery) is None
    bigquery.reset_mock()

    sheet.cell_range = "A1:B2"
    import_table_from_sheet(table, sheet)
    assert get_cell_range_from_job(bigquery) == sheet.cell_range
    bigquery.reset_mock()

    sheet.sheet_name = "Easy"
    import_table_from_sheet(table, sheet)
    assert get_cell_range_from_job(bigquery) == f"{sheet.sheet_name}!{sheet.cell_range}"
    bigquery.reset_mock()

    sheet.cell_range = None
    import_table_from_sheet(table, sheet)
    assert get_cell_range_from_job(bigquery) == sheet.sheet_name
