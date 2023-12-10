from functools import lru_cache

from django.conf import settings

from apps.base.engine.bigquery import BigQueryClient
from apps.base.engine.postgres import PostgresClient


def get_backend_name():
    if settings.DATABASE_URL and settings.DATABASE_URL.startswith("postgresql://"):
        return "postgres"
    return "bigquery"


@lru_cache
def get_backend_client():
    if get_backend_name() == "postgres":
        return PostgresClient()
    return BigQueryClient()
