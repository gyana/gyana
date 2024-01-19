from functools import lru_cache

from django.conf import settings
from django.utils.text import slugify
from google.cloud import storage
from googleapiclient import discovery

from apps.base.engine.bigquery import BigQueryClient
from apps.base.engine.credentials import get_credentials
from apps.base.engine.postgres import PostgresClient

from .core.bigquery import *  # noqa
from .core.ibis.bigquery import *  # noqa
from .core.ibis.client import *  # noqa
from .core.ibis.compiler import *  # noqa

SLUG = (
    slugify(settings.CLOUD_NAMESPACE) if settings.CLOUD_NAMESPACE is not None else None
)


@lru_cache
def get_engine():
    engine_url = settings.ENGINE_URL

    if engine_url.startswith("postgresql://"):
        return PostgresClient(engine_url)

    if engine_url.startswith("bigquery://"):
        return BigQueryClient(engine_url)

    raise ValueError(f"Gyana doesnt not support this engine URL {engine_url}")


@lru_cache
def sheets():
    credentials, _ = get_credentials()

    return discovery.build("sheets", "v4", credentials=credentials)


@lru_cache
def drive_v2():
    credentials, _ = get_credentials()

    # latest v3 client does not return all metadata for file
    return discovery.build("drive", "v2", credentials=credentials)


@lru_cache()
def get_bucket():
    client = storage.Client()
    return client.get_bucket(settings.GS_BUCKET_NAME)
