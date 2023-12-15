from functools import lru_cache
from typing import TYPE_CHECKING

import ibis
import sqlalchemy as sa
from django.conf import settings
from pandas import DataFrame, read_csv, read_json
from sqlalchemy import create_engine, inspect

from apps.base.engine.base import BaseClient

if TYPE_CHECKING:
    from apps.customapis.models import CustomApi
    from apps.tables.models import Table
    from apps.teams.models import Team
    from apps.uploads.models import Upload


@lru_cache
def postgres():
    return create_engine(settings.DATABASE_URL)


class PostgresClient(BaseClient):
    def __init__(self):
        self.client = ibis.postgres.connect(url=settings.DATABASE_URL)

    def _df_to_sql(self, df: DataFrame, table_name: str, schema: str):
        sa_client = postgres()
        inspector = inspect(sa_client)

        if schema not in inspector.get_schema_names():
            with sa_client.connect() as conn:
                conn.execute(sa.schema.CreateSchema(schema))
                conn.commit()
        df.to_sql(
            table_name,
            con=sa_client,
            schema=schema,
            if_exists="replace",
            index=False,
        )

    def get_table(self, table: "Table"):
        return self.client.table(
            table.bq_table,
            schema=table.bq_dataset,
        )

    def import_table_from_upload(self, table: "Table", upload: "Upload"):
        df = read_csv(upload.gcs_uri)

        self._df_to_sql(df, table.bq_table, table.bq_dataset)

    def create_team_dataset(self, team: "Team"):
        self.client.create_schema(team.tables_dataset_id, force=True)

    def delete_team_dataset(self, team: "Team"):
        self.client.drop_schema(team.tables_dataset_id, force=True)

    def import_table_from_customapi(self, table: "Table", customapi: "CustomApi"):
        df = read_json(customapi.gcs_uri)

        self._df_to_sql(df, table.bq_table, table.bq_dataset)
