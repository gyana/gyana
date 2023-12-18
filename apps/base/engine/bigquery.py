import re
from functools import lru_cache
from typing import TYPE_CHECKING

import ibis
from django.conf import settings
from google.cloud import bigquery as bq

from apps.base.core.bigquery import (
    bq_table_schema_is_string_only,
    sanitize_bq_column_name,
)
from apps.base.core.utils import excel_colnum_string
from apps.base.engine.base import BaseClient

from .credentials import get_credentials

if TYPE_CHECKING:
    from apps.customapis.models import CustomApi
    from apps.sheets.models import Sheet
    from apps.tables.models import Table
    from apps.teams.models import Team
    from apps.uploads.models import Upload


def _create_external_table(upload: "Upload", table_id: str, **job_kwargs):
    # https://cloud.google.com/bigquery/external-data-drive#python
    external_config = bq.ExternalConfig("CSV")
    external_config.source_uris = [upload.gcs_uri]
    external_config.options.field_delimiter = upload.field_delimiter_char
    external_config.options.allow_quoted_newlines = True
    external_config.options.allow_jagged_rows = True

    for k, v in job_kwargs.items():
        if k == "skip_leading_rows":
            setattr(external_config.options, k, v)
        else:
            setattr(external_config, k, v)

    return bq.QueryJobConfig(table_definitions={table_id: external_config})


def _load_table(upload: "Upload", table: "Table", client, **job_kwargs):
    job_config = bq.LoadJobConfig(
        source_format=bq.SourceFormat.CSV,
        write_disposition=bq.WriteDisposition.WRITE_TRUNCATE,
        field_delimiter=upload.field_delimiter_char,
        allow_quoted_newlines=True,
        allow_jagged_rows=True,
        **job_kwargs,
    )

    load_job = client.load_table_from_uri(
        upload.gcs_uri, table.bq_id, job_config=job_config
    )

    if load_job.exception():
        raise Exception(load_job.errors[0]["message"])


def _create_external_table_sheet(
    sheet: "Sheet", table_id: str, **job_kwargs
) -> bq.ExternalConfig:
    """
    Constructs a BQ external config.

    For a Google Sheets integration `url` is required and `cell_range` is optional
    """

    # https://cloud.google.com/bigquery/external-data-drive#python
    from apps.sheets.sheets import get_cell_range

    external_config = bq.ExternalConfig("GOOGLE_SHEETS")
    external_config.source_uris = [sheet.url]
    if sheet.sheet_name or sheet.cell_range:
        external_config.options.range = get_cell_range(
            sheet.sheet_name, sheet.cell_range
        )
    for k, v in job_kwargs.items():
        if k == "skip_leading_rows":
            setattr(external_config.options, k, v)
        else:
            setattr(external_config, k, v)

    return bq.QueryJobConfig(
        table_definitions={
            table_id: external_config,
        }
    )


CONVERSION_ERROR = re.compile(
    "Could not convert value to (.*). Row ([0-9]*); Col ([0-9]*)"
)


def _load_table_sheet(sheet: "Sheet", table: "Table", **job_kwargs):
    client = bigquery()

    external_table_id = f"{table.bq_table}_external"

    query_job = client.query(
        f"CREATE OR REPLACE TABLE {table.bq_id} AS SELECT * FROM {external_table_id}",
        job_config=_create_external_table_sheet(sheet, external_table_id, **job_kwargs),
    )

    # capture external table creation errors

    if query_job.exception():
        error_message = query_job.errors[0]["message"]
        if re.search(CONVERSION_ERROR, error_message):
            type_, row, col = re.search(CONVERSION_ERROR, error_message).groups()
            error_message = (
                f"We could not convert cell {excel_colnum_string(int(col)+1)}{int(row)+1} to {type_}."
                f"Try changing the cell value to the appropiate format and retry the sync."
            )
        raise Exception(error_message)


@lru_cache
def bigquery():
    # https://cloud.google.com/bigquery/external-data-drive#python
    credentials, project = get_credentials()

    # return bigquery.Client(project=settings.GCP_PROJECT)
    return bq.Client(
        credentials=credentials, project=project, location=settings.BIGQUERY_LOCATION
    )


class BigQueryClient(BaseClient):
    def __init__(self):
        self.client = ibis.bigquery.connect(
            project_id=settings.GCP_PROJECT, auth_external_data=True
        )

    def get_table(self, table: "Table"):
        return self.client.table(table.bq_id, database=table.bq_dataset)

    def _get_bigquery_object(self, bq_id):
        return bigquery().get_table(bq_id)

    def import_table_from_upload(self, table: "Table", upload: "Upload"):
        client = bigquery()
        _load_table(upload, table, client, autodetect=True, skip_leading_rows=1)

        # bigquery does not autodetect the column names if all columns are strings
        # https://cloud.google.com/bigquery/docs/schema-detect#csv_header
        # the recommended approach for cost is to reload into bigquery rather than updating names
        # https://cloud.google.com/bigquery/docs/manually-changing-schemas#option_2_exporting_your_data_and_loading_it_into_a_new_table

        if bq_table_schema_is_string_only(self._get_bigquery_object(table.bq_id)):
            # create temporary table without skipping the header row, so we can get the header names

            temp_table_id = f"{table.bq_table}_temp"

            job_config = _create_external_table(
                upload, temp_table_id, autodetect=True, skip_leading_rows=0
            )

            # bigquery does not guarantee the order of rows
            header_query = client.query(
                f"select * from (select * from {temp_table_id} except distinct select * from {table.bq_id}) limit 1",
                job_config=job_config,
            )

            header_rows = list(header_query.result())
            if len(header_rows) == 0:
                raise Exception(
                    "Error: We weren't able to automatically detect the schema of your upload."
                )

            header_values = header_rows[0].values()

            # use the header row to provide an explicit schema

            _load_table(
                upload,
                table,
                client,
                skip_leading_rows=1,
                schema=[
                    bq.SchemaField(sanitize_bq_column_name(field), "STRING")
                    for field in header_values
                ],
            )

        return

    def create_or_replace_table(self, table_id: str, query):
        # TODO: Update to ibis 7 to support create_table with overwrite=True
        self.client.raw_sql(f"CREATE OR REPLACE TABLE {table_id} as " f"({query})")

    def create_team_dataset(self, team: "Team"):
        client = bigquery()
        # exists ok is for testing
        client.create_dataset(team.tables_dataset_id, exists_ok=True)

    def delete_team_dataset(self, team: "Team"):
        client = bigquery()
        client.delete_dataset(
            team.tables_dataset_id, delete_contents=True, not_found_ok=True
        )

    def import_table_from_customapi(self, table: "Table", customapi: "CustomApi"):
        client = bigquery()

        job_config = bq.LoadJobConfig(
            source_format=bq.SourceFormat.NEWLINE_DELIMITED_JSON,
            write_disposition=bq.WriteDisposition.WRITE_TRUNCATE,
            autodetect=True,
        )

        load_job = client.load_table_from_uri(
            customapi.gcs_uri, table.bq_id, job_config=job_config
        )

        if load_job.exception():
            raise Exception(load_job.errors[0]["message"])

    def drop_table(self, table_id: str):
        return bigquery().delete_table(table_id, not_found_ok=True)

    def get_modified_and_num_rows(self, table: "Table"):
        bq_obj = self._get_bigquery_object(table.bq_id)
        return bq_obj.modified, bq_obj.num_rows

    def import_table_from_sheet(self, table: "Table", sheet: "Sheet"):
        """
        Copy Google Sheet to BigQuery table via temporary external table.
        Having data in a bq table rather than an external source makes using it much faster.

        https://cloud.google.com/bigquery/docs/tables-intro
        """

        client = bigquery()

        _load_table_sheet(sheet, table, autodetect=True)

        # see apps/uploads/bigquery.py for motivation

        if bq_table_schema_is_string_only(self._get_bigquery_object(table.bq_id)):
            # create temporary table but skipping the header rows

            temp_table_id = f"{table.bq_table}_temp"

            job_config = _create_external_table_sheet(
                sheet, temp_table_id, autodetect=True, skip_leading_rows=1
            )

            # bigquery does not guarantee the order of rows

            header_query = client.query(
                f"select * from (select * from {table.bq_id} except distinct select * from {temp_table_id}) limit 1",
                job_config=job_config,
            )

            header_rows = list(header_query.result())
            if len(header_rows) == 0:
                raise Exception(
                    "Error: We weren't able to automatically detect the schema of your sheet."
                )

            header_values = header_rows[0].values()

            # use the header row to provide an explicit schema

            _load_table_sheet(
                sheet,
                table,
                skip_leading_rows=1,
                schema=[
                    bq.SchemaField(sanitize_bq_column_name(field), "STRING")
                    for field in header_values
                ],
            )
