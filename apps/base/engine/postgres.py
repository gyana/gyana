from functools import lru_cache
from typing import TYPE_CHECKING

import ibis
import sqlalchemy as sa
from django.conf import settings
from pandas import read_csv
from sqlalchemy import create_engine, inspect

from apps.base.engine.base import BaseClient

if TYPE_CHECKING:
    from apps.tables.models import Table
    from apps.uploads.models import Upload


@lru_cache
def postgres():
    return create_engine(settings.DATABASE_URL)


class PostgresClient(BaseClient):
    def __init__(self):
        self.client = ibis.postgres.connect(url=settings.DATABASE_URL)

    def get_table(self, table: "Table"):
        return self.client.table(
            table.bq_table,
            schema=table.bq_dataset,
        )

    def import_table_from_upload(self, table: "Table", upload: "Upload"):
        df = read_csv(upload.gcs_uri)
        sa_client = postgres()
        inspector = inspect(sa_client)
        if table.bq_dataset not in inspector.get_schema_names():
            with sa_client.connect() as conn:
                conn.execute(sa.schema.CreateSchema(table.bq_dataset))
                conn.commit()

        df.to_sql(
            table.bq_table,
            con=sa_client,
            schema=table.bq_dataset,
            if_exists="replace",
            index=False,
        )
