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

    def get_table(self, table: "Table"):
        return self.client.table(
            table.bq_table,
            schema=table.bq_dataset,
        )

    def create_team_dataset(self, team: "Team"):
        self.client.create_schema(team.tables_dataset_id, force=True)

    def delete_team_dataset(self, team: "Team"):
        self.client.drop_schema(team.tables_dataset_id, force=True)

    def create_or_replace_table(self, table_id: str, query: str):
        # TODO: Update to ibis 7 to support create_tablr with overwrite=True
        self.client.raw_sql(f"CREATE OR REPLACE TABLE {table_id} as ({query})")

    def drop_table(self, table_id: str):
        self.client.drop_table(table_id, force=True)

    def get_modified_and_num_rows(self, table: "Table"):
        modified = timezone.now()
        num_rows = self.get_table(table).count().execute()
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
