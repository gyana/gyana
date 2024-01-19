from functools import lru_cache

import ibis
from sqlalchemy import create_engine

from apps.base.engine.base import BaseClient


@lru_cache
def postgres(engine_url):
    return create_engine(engine_url)


class PostgresClient(BaseClient):
    excluded_nodes = ["pivot", "unpivot"]

    def __init__(self, engine_url):
        super().__init__(engine_url)

        self.client = ibis.postgres.connect(url=self.engine_url)
        self.raw_client = postgres(self.engine_url)
