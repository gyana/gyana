import pytest

from apps.base.clients import get_engine

pytestmark = pytest.mark.django_db


def test_sheet_all_string(
    project, mock_bigquery, mock_bq_query, sheet_factory, integration_table_factory
):
    sheet = sheet_factory(integration__project=project)
    table = integration_table_factory(project=project, integration=sheet.integration)

    get_engine().import_table_from_sheet(table, sheet)

    # initial call has result with strings
    initial_call = mock_bq_query.call_args_list[0]
    INTIAL_SQL = "CREATE OR REPLACE TABLE dataset.table AS SELECT * FROM table_external"
    assert initial_call.args == (INTIAL_SQL,)
    job_config = initial_call.kwargs["job_config"]
    external_config = job_config.table_definitions["table_external"]
    assert external_config.source_uris == [sheet.url]
    assert external_config.autodetect
    assert external_config.options.range == sheet.cell_range

    # header call is to a temporary table with skipped leading rows
    header_call = mock_bq_query.call_args_list[1]
    HEADER_SQL = "select * from (select * from dataset.table except distinct select * from table_temp) limit 1"
    assert header_call.args == (HEADER_SQL,)
    job_config = header_call.kwargs["job_config"]
    external_config = job_config.table_definitions["table_temp"]
    assert external_config.source_uris == [sheet.url]
    assert external_config.autodetect
    assert external_config.options.range == sheet.cell_range
    assert external_config.options.skip_leading_rows == 1

    # final call with explicit schema
    final_call = mock_bq_query.call_args_list[2]
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


def get_cell_range_from_job(mock_bq_query):
    return (
        mock_bq_query.call_args_list[0]
        .kwargs["job_config"]
        .table_definitions["table_external"]
        .options.range
    )


def test_cell_range_construction(
    project, mock_bigquery, mock_bq_query, sheet_factory, integration_table_factory
):
    sheet = sheet_factory(integration__project=project, cell_range=None)
    table = integration_table_factory(project=project, integration=sheet.integration)

    get_engine().import_table_from_sheet(table, sheet)
    assert get_cell_range_from_job(mock_bq_query) is None
    mock_bq_query.reset_mock()

    sheet.cell_range = "A1:B2"
    get_engine().import_table_from_sheet(table, sheet)
    assert get_cell_range_from_job(mock_bq_query) == sheet.cell_range
    mock_bq_query.reset_mock()

    sheet.sheet_name = "Easy"
    get_engine().import_table_from_sheet(table, sheet)
    assert (
        get_cell_range_from_job(mock_bq_query)
        == f"{sheet.sheet_name}!{sheet.cell_range}"
    )
    mock_bq_query.reset_mock()

    sheet.cell_range = None
    get_engine().import_table_from_sheet(table, sheet)
    assert get_cell_range_from_job(mock_bq_query) == sheet.sheet_name
