import json
import os
from datetime import datetime
from functools import cache
from glob import glob

from django.urls.base import reverse
from django.utils import timezone

from ..models import Connector

SCHEMA_FIXTURES_DIR = "apps/connectors/fivetran/fixtures"
MOCK_SCHEMA_DIR = os.path.abspath(".mock/.schema")


def get_connector_json(connector, is_historical_sync=False, succeeded_at=None):

    if succeeded_at is not None:
        succeeded_at = datetime.strftime(succeeded_at, "%Y-%m-%dT%H:%M:%S.%f%z")

    return {
        "id": connector.fivetran_id,
        "group_id": "group_id",
        "service": connector.service,
        "service_version": 4,
        "schema": connector.schema,
        "paused": True,
        "pause_after_trial": True,
        "connected_by": "monitoring_assuring",
        "created_at": "2021-01-01T00:00:00.000000Z",
        "succeeded_at": succeeded_at,
        "failed_at": None,
        "sync_frequency": 360,
        "schedule_type": "auto",
        "status": {
            "setup_state": "connected",
            "sync_state": "scheduled",
            "update_state": "delayed",
            "is_historical_sync": is_historical_sync,
            "tasks": [],
            "warnings": [],
        },
        "config": {},
    }


@cache
def get_fixture_fivetran_ids():
    return [
        f["fields"]["fivetran_id"]
        for f in json.load(open("cypress/fixtures/fixtures.json", "r"))
        if f["model"] == "connectors.connector"
    ]


# enables celery to read updated mock config
class MockSchemaStore:
    def __setitem__(self, key, value):
        json.dump(value, open(f"{MOCK_SCHEMA_DIR}/{key}.json", "w"))

    def __getitem__(self, key):
        return json.load(open(f"{MOCK_SCHEMA_DIR}/{key}.json", "r"))

    def __contains__(self, key) -> bool:
        return f"{key}.json" in os.listdir(MOCK_SCHEMA_DIR)

    def clear(self):
        for f in glob(f"{MOCK_SCHEMA_DIR}/*"):
            os.remove(f)


class MockFivetranClient:

    # default if not available in fixtures
    DEFAULT_SERVICE = "google_analytics"
    # wait 1s if refreshing page, otherwise 5 seconds for task to complete
    REFRESH_SYNC_SECONDS = 1
    BLOCK_SYNC_SECONDS = 5

    def __init__(self) -> None:
        # stored as dict to test that logic
        self._schema_cache = MockSchemaStore()
        self._started = {}

    def create(self, service, team_id, daily_sync_time):
        # duplicate the content of the first created existing connector
        connector = (
            Connector.objects.filter(service=service).order_by("id").first()
            or Connector.objects.filter(service=self.DEFAULT_SERVICE).first()
        )
        return get_connector_json(connector, is_historical_sync=True)

    def get(self, connector):
        started = self._started.get(connector.id)
        is_historical_sync = (
            (timezone.now() - started).total_seconds() < self.REFRESH_SYNC_SECONDS
            if started is not None
            else False
        )
        succeeded_at = timezone.now() if not is_historical_sync else None

        return get_connector_json(
            connector, is_historical_sync=is_historical_sync, succeeded_at=succeeded_at
        )

    def list(self):
        for connector in Connector.objects.all():
            yield self.get(connector)

    def update(self, connector, **data):
        pass

    def start_initial_sync(self, connector):
        self._started[connector.id] = timezone.now()

    def start_update_sync(self, connector):
        self._started[connector.id] = timezone.now()

    def get_authorize_url(self, connector, redirect_uri):
        return f"{reverse('connectors:mock')}?redirect_uri={redirect_uri}"

    def reload_schemas(self, connector):
        pass

    def get_schemas(self, connector):
        if connector.id in self._schema_cache:
            return self._schema_cache[connector.id]

        service = connector.service if connector is not None else "google_analytics"
        fivetran_id = connector.fivetran_id if connector is not None else "humid_rifle"

        with open(f"{SCHEMA_FIXTURES_DIR}/{service}_{fivetran_id}.json", "r") as f:
            return json.load(f)

    def update_schemas(self, connector, schemas):
        self._schema_cache[connector.id] = schemas

    def delete(self, connector):
        pass
