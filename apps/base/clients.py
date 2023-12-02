from abc import ABC, abstractmethod
from functools import lru_cache
from typing import TYPE_CHECKING

import google.auth
import ibis
import sqlalchemy as sa
from django.conf import settings
from django.utils.text import slugify
from google.cloud import bigquery as bigquery_client
from google.cloud import storage
from googleapiclient import discovery
from pandas import read_csv
from sqlalchemy import create_engine, inspect

from ._bigquery_upload import (
    import_table_from_upload as bigquery_import_table_from_upload,
)
from .core.bigquery import *  # noqa
from .core.ibis.client import *  # noqa
from .core.ibis.compiler import *  # noqa

if TYPE_CHECKING:
    from apps.tables.models import Table
    from apps.uploads.models import Upload

SLUG = (
    slugify(settings.CLOUD_NAMESPACE) if settings.CLOUD_NAMESPACE is not None else None
)

# BigQuery jobs are limited to 6 hours runtime
BIGQUERY_JOB_LIMIT = 6 * 60 * 60


def get_credentials():
    return google.auth.default(
        scopes=[
            "https://www.googleapis.com/auth/drive",
            "https://www.googleapis.com/auth/bigquery",
        ]
    )


@lru_cache
def sheets():
    credentials, _ = get_credentials()

    return discovery.build("sheets", "v4", credentials=credentials)


@lru_cache
def drive_v2():
    credentials, _ = get_credentials()

    # latest v3 client does not return all metadata for file
    return discovery.build("drive", "v2", credentials=credentials)


@lru_cache
def bigquery():
    # https://cloud.google.com/bigquery/external-data-drive#python
    credentials, project = get_credentials()

    # return bigquery.Client(project=settings.GCP_PROJECT)
    return bigquery_client.Client(
        credentials=credentials, project=project, location=settings.BIGQUERY_LOCATION
    )


@lru_cache
def postgres():
    return create_engine(settings.DATABASE_URL)


def get_backend_name():
    if settings.DATABASE_URL and settings.DATABASE_URL.startswith("postgresql://"):
        return "postgres"
    return "bigquery"


@lru_cache
def get_backend_client():
    if get_backend_name() == "postgres":
        return PostgresClient()
    return BigQueryClient()


@lru_cache
def ibis_client():
    return get_backend_client().client


@lru_cache()
def get_bucket():
    client = storage.Client()
    return client.get_bucket(settings.GS_BUCKET_NAME)


class BaseClient(ABC):
    @abstractmethod
    def get_table(self, table: "Table"):
        raise NotImplementedError

    @abstractmethod
    def import_table_from_upload(self, table: "Table", upload: "Upload"):
        raise NotImplementedError


class BigQueryClient(BaseClient):
    def __init__(self):
        self.client = ibis.bigquery.connect(
            project_id=settings.GCP_PROJECT, auth_external_data=True
        )

    def get_table(self, table: "Table"):
        return self.client.table(table.bq_id, database=table.bq_dataset)

    def import_table_from_upload(self, table: "Table", upload: "Upload"):
        return bigquery_import_table_from_upload(table, upload, bigquery())


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
