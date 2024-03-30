import pytest

from apps.base.clients import get_engine

pytestmark = pytest.mark.django_db


def test_upload_all_string(
    logged_in_user,
    engine,
    upload_factory,
    integration_table_factory,
):
    upload = upload_factory(integration__project__team=logged_in_user.teams.first())
    table = integration_table_factory(
        project=upload.integration.project, integration=upload.integration
    )

    get_engine().import_table_from_upload(table, upload)

    # initial call has result with strings
    initial_call = engine.load_table_from_uri.call_args_list[0]
    assert initial_call.args == (upload.gcs_uri, table.fqn)
    job_config = initial_call.kwargs["job_config"]
    assert job_config.source_format == "CSV"
    assert job_config.write_disposition == "WRITE_TRUNCATE"
    assert job_config.field_delimiter == upload.field_delimiter_char
    assert job_config.allow_quoted_newlines
    assert job_config.allow_jagged_rows
    assert job_config.autodetect
    assert job_config.skip_leading_rows == 1

    # header call is to a temporary table with skipped leading rows
    header_call = engine.query.call_args_list[0]
    HEADER_SQL = "select * from (select * from table_temp except distinct select * from dataset.table) limit 1"
    assert header_call.args == (HEADER_SQL,)
    job_config = header_call.kwargs["job_config"]
    external_config = job_config.table_definitions["table_temp"]
    assert external_config.source_uris == [upload.gcs_uri]
    assert external_config.options.field_delimiter == upload.field_delimiter_char
    assert external_config.options.allow_quoted_newlines
    assert external_config.options.allow_jagged_rows
    assert external_config.autodetect
    assert external_config.options.skip_leading_rows == 0

    # final call with explicit schema
    final_call = engine.load_table_from_uri.call_args_list[1]
    assert final_call.args == (upload.gcs_uri, table.fqn)
    job_config = final_call.kwargs["job_config"]
    assert job_config.source_format == "CSV"
    assert job_config.write_disposition == "WRITE_TRUNCATE"
    assert job_config.field_delimiter == upload.field_delimiter_char
    assert job_config.allow_quoted_newlines
    assert job_config.allow_jagged_rows
    assert job_config.skip_leading_rows == 1
    schema = job_config.schema
    assert schema is not None
    assert len(schema) == 2
    assert schema[0].name == "Name"
    assert schema[0].field_type == "STRING"
