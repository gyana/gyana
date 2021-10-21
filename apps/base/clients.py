from functools import lru_cache

import google.auth
import heroku3
import ibis_bigquery
from django.conf import settings
from django.utils.text import slugify
from google.cloud import bigquery, storage
from googleapiclient import discovery

from .bigquery import *
from .ibis.client import *
from .ibis.compiler import *
from .ibis.patch import *

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
def sheets_client():
    credentials, _ = get_credentials()

    return discovery.build("sheets", "v4", credentials=credentials)


@lru_cache
def drive_v2_client():
    credentials, _ = get_credentials()

    # latest v3 client does not return all metadata for file
    return discovery.build("drive", "v2", credentials=credentials)


@lru_cache
def bigquery_client():
    # https://cloud.google.com/bigquery/external-data-drive#python
    credentials, project = get_credentials()

    # return bigquery.Client(project=settings.GCP_PROJECT)
    return bigquery.Client(
        credentials=credentials, project=project, location=settings.BIGQUERY_LOCATION
    )


@lru_cache
def ibis_client():
    return ibis_bigquery.connect(
        project_id=settings.GCP_PROJECT, auth_external_data=True
    )


@lru_cache()
def get_bucket():
    client = storage.Client()
    return client.get_bucket(settings.GS_BUCKET_NAME)


def get_dataframe(query):
    client = bigquery_client()
    return client.query(query).result().to_dataframe(create_bqstorage_client=False)


@lru_cache
def fivetran():
    from apps.connectors.fivetran.client import FivetranClient

    return FivetranClient()


@lru_cache
def heroku_client():
    heroku_conn = heroku3.from_key(settings.HEROKU_API_KEY)
    return heroku_conn.app(settings.HEROKU_APP)
