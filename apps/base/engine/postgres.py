from functools import lru_cache

import ibis
from django.conf import settings
from sqlalchemy import create_engine

from apps.base.engine.base import BaseClient


@lru_cache
def postgres():
    return create_engine(settings.ENGINE_URL)


class PostgresClient(BaseClient):
    def __init__(self):
        self.client = ibis.postgres.connect(url=settings.ENGINE_URL)
        self.raw_client = postgres()
