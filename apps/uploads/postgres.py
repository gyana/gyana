import sqlalchemy as sa
from pandas import read_csv
from sqlalchemy import inspect

from apps.base import clients
from apps.tables.models import Table

from .models import Upload


def import_table_from_upload(table: Table, upload: Upload):
    df = read_csv(upload.gcs_uri)
    postgres = clients.postgres()
    inspector = inspect(postgres)
    if table.bq_dataset not in inspector.get_schema_names():
        with postgres.connect() as conn:
            conn.execute(sa.schema.CreateSchema(table.bq_dataset))
            conn.commit()

    df.to_sql(
        table.bq_table,
        con=postgres,
        schema=table.bq_dataset,
        if_exists="replace",
        index=False,
    )
