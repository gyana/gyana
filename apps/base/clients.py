from functools import lru_cache

from django.conf import settings
from django.utils.text import slugify
from google.cloud import storage
from googleapiclient import discovery

from apps.base.engine.bigquery import get_credentials

from .core.bigquery import *  # noqa
from .core.ibis.client import *  # noqa
from .core.ibis.compiler import *  # noqa

SLUG = (
    slugify(settings.CLOUD_NAMESPACE) if settings.CLOUD_NAMESPACE is not None else None
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


@lru_cache()
def get_bucket():
    client = storage.Client()
    return client.get_bucket(settings.GS_BUCKET_NAME)
