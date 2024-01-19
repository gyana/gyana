import re
from abc import ABC
from typing import TYPE_CHECKING

import ibis
import sqlalchemy as sa
from django.utils import timezone
from pandas import DataFrame, read_csv, read_json
from sqlalchemy import inspect

from ._sheet import create_dataframe_from_sheet

if TYPE_CHECKING:
    from apps.customapis.models import CustomApi
    from apps.sheets.models import Sheet
    from apps.tables.models import Table
    from apps.teams.models import Team
    from apps.uploads.models import Upload


class BaseClient(ABC):
    client: ibis.BaseBackend
    raw_client: sa.Engine
    excluded_nodes = []

    def __init__(self, engine_url) -> None:
        super().__init__()
        self.engine_url = engine_url

    def get_table(self, table: "Table"):
        return self.client.table(
            table.bq_table,
            schema=table.bq_dataset,
        )

    def create_team_dataset(self, team: "Team"):
        self.client.raw_sql(f"CREATE SCHEMA {team.tables_dataset_id}")
        # TODO: Use this once upgraded to Ibis 7.0
        # self.client.create_schema(team.tables_dataset_id, force=True)

    def delete_team_dataset(self, team: "Team"):
        self.client.raw_sql(f"DROP SCHEMA {team.tables_dataset_id}")
        # TODO: Use this once upgraded to Ibis 7.0
        # self.client.drop_schema(team.tables_dataset_id, force=True)

    def create_or_replace_table(self, table_id: str, query):
        # SQLAlchemy backends return an SQLAlchemy object
        # Might be able to remove after upgradin ibis that introduces
        # a sql method
        if not isinstance(query, str):
            query = str(query.compile(compile_kwargs={"literal_binds": True})).replace(
                "\n", ""
            )
        with self.raw_client.connect() as conn:
            # TODO: Update to ibis 7 to support create_table with overwrite=True
            conn.execute(sa.text(f"DROP TABLE IF EXISTS {table_id}"))
            conn.execute(sa.text(f"CREATE TABLE {table_id} as ({query})"))
            conn.commit()

    def drop_table(self, table_id: str):
        self.client.drop_table(table_id, force=True)

    def get_table_size(self, table: "Table"):
        return self.get_table(table).count().execute()

    def get_source_metadata(self, table: "Table"):
        # by default, Postgres does not support last modified time on tables
        # so we just take the current timestamp to be safe
        modified = timezone.now()
        # requires an extra query on the table, may be slow for large tables
        # TODO: possibly add option to disable num_row tracking
        num_rows = self.get_table_size(table)
        return modified, num_rows

    def import_table_from_upload(self, table: "Table", upload: "Upload"):
        # TODO: Potentially can use ibis client read_csv when updating ibis
        df = read_csv(upload.gcs_uri)

        self._df_to_sql(df, table.bq_table, table.bq_dataset)

    def import_table_from_customapi(self, table: "Table", customapi: "CustomApi"):
        # TODO: Potentially can use ibis client read_json when updating ibis
        df = read_json(customapi.gcs_uri, lines=True)

        self._df_to_sql(df, table.bq_table, table.bq_dataset)

    def import_table_from_sheet(self, table: "Table", sheet: "Sheet"):
        df = create_dataframe_from_sheet(sheet)

        self._df_to_sql(df, table.bq_table, table.bq_dataset)

    def _df_to_sql(self, df: DataFrame, table_name: str, schema: str):
        inspector = inspect(self.raw_client)

        if schema not in inspector.get_schema_names():
            with self.raw_client.connect() as conn:
                conn.execute(sa.schema.CreateSchema(schema))
                conn.commit()

        df.to_sql(
            table_name,
            con=self.raw_client,
            schema=schema,
            if_exists="replace",
            index=False,
        )

    def copy_table(self, from_table, to_table):
        """Copies a bigquery table from `from_table` to `to_table.

        Replaces if the table already exists, mostly important to work locally,
        in prod that shouldn't be necessary.
        """
        return self.create_or_replace_table(to_table, f"SELECT * FROM {from_table}")

    def export_to_csv(self, query, gcs_path):
        """Exports a query to a csv on GCS"""

        df = query.execute()
        df.to_csv(gcs_path, index=False)

    def get_dashboard_url(self):
        # only implemented for BigQuery
        return None
