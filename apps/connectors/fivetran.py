import json
import os
import time
import uuid
from dataclasses import asdict, dataclass
from functools import cache
from glob import glob
from typing import Dict, List, Optional

import backoff
import requests
from django.conf import settings
from django.http import HttpResponse
from django.shortcuts import redirect
from django.urls.base import reverse
from django.utils import timezone

from .config import get_services
from .models import Connector

# wrapper for the Fivetran connectors REST API, documented here
# https://fivetran.com/docs/rest-api/connectors
# on error, raise a FivetranClientError and it will be managed in
# the caller (e.g. form) or trigger 500 (user can refresh/retry)


@dataclass
class FivetranTable:
    key: str
    name_in_destination: str
    enabled: bool
    enabled_patch_settings: Dict
    columns: Optional[List[Dict]] = None

    def asdict(self):
        res = asdict(self)
        res.pop("key")
        if self.columns is None:
            res.pop("columns")
        return res


@dataclass
class FivetranSchema:
    key: str
    name_in_destination: str
    enabled: bool
    tables: List[FivetranTable]

    def __post_init__(self):
        self.tables = [FivetranTable(key=k, **t) for k, t in self.tables.items()]

    def asdict(self):
        res = {**asdict(self), "tables": {t.key: t.asdict() for t in self.tables}}
        res.pop("key")
        return res

    @property
    def enabled_bq_ids(self):
        return {
            f"{self.name_in_destination}.{table.name_in_destination}"
            for table in self.tables
            if table.enabled and self.enabled
        }


def _schemas_to_obj(schemas_dict):
    return [FivetranSchema(key=k, **s) for k, s in schemas_dict.items()]


def _schemas_to_dict(schemas):
    return {s.key: s.asdict() for s in schemas}


class FivetranClientError(Exception):
    pass


class FivetranClient:
    def create(self, service, team_id) -> Dict:
        from apps.base.clients import SLUG

        # https://fivetran.com/docs/rest-api/connectors#createaconnector

        service_conf = get_services()[service]

        config = service_conf["static_config"] or {}

        # https://fivetran.com/docs/rest-api/connectors/config
        # database connectors require schema_prefix, rather than schema

        schema = f"team_{team_id:06}_{service}_{uuid.uuid4().hex}"
        if SLUG:
            schema = f"{SLUG}_{schema}"

        config[
            "schema_prefix"
            if service_conf["requires_schema_prefix"] == "t"
            else "schema"
        ] = schema

        res = requests.post(
            f"{settings.FIVETRAN_URL}/connectors",
            json={
                "service": service,
                "group_id": settings.FIVETRAN_GROUP,
                # no access credentials yet
                "run_setup_tests": False,
                "paused": True,
                "config": config,
            },
            headers=settings.FIVETRAN_HEADERS,
        ).json()

        if res["code"] != "Success":
            raise FivetranClientError(res["message"])

        # response schema https://fivetran.com/docs/rest-api/connectors#response_1
        #  {
        #   "code": "Success",
        #   "message": "Connector has been created",
        #   "data": {
        #       "id": "{{ fivetran_id }}",
        #       # returns odd results for Google Sheets
        #       "schema": "{{ schema }}",
        #       ...
        #    }
        #  }
        return {"fivetran_id": res["data"]["id"], "schema": schema}

    def authorize(self, connector: Connector, redirect_uri: str) -> HttpResponse:

        # https://fivetran.com/docs/rest-api/connectors/connect-card#connectcard

        card = requests.post(
            f"{settings.FIVETRAN_URL}/connectors/{connector.fivetran_id}/connect-card-token",
            headers=settings.FIVETRAN_HEADERS,
        )
        connect_card_token = card.json()["token"]

        return redirect(
            f"https://fivetran.com/connect-card/setup?redirect_uri={redirect_uri}&auth={connect_card_token}"
        )

    def start_initial_sync(self, connector: Connector) -> Dict:

        # https://fivetran.com/docs/rest-api/connectors#modifyaconnector

        res = requests.patch(
            f"{settings.FIVETRAN_URL}/connectors/{connector.fivetran_id}",
            json={"paused": False},
            headers=settings.FIVETRAN_HEADERS,
        ).json()

        if res["code"] != "Success":
            raise FivetranClientError()

        return res

    def start_update_sync(self, connector: Connector) -> Dict:

        # https://fivetran.com/docs/rest-api/connectors#syncconnectordata

        res = requests.post(
            f"{settings.FIVETRAN_URL}/connectors/{connector.fivetran_id}/force",
            headers=settings.FIVETRAN_HEADERS,
        ).json()

        if res["code"] != "Success":
            raise FivetranClientError()

        return res

    def has_completed_sync(self, connector: Connector) -> bool:

        res = requests.get(
            f"{settings.FIVETRAN_URL}/connectors/{connector.fivetran_id}",
            headers=settings.FIVETRAN_HEADERS,
        ).json()

        if res["code"] != "Success":
            raise FivetranClientError()

        status = res["data"]["status"]

        return not (status["is_historical_sync"] or status["sync_state"] == "syncing")

    def block_until_synced(self, connector: Connector):

        backoff.on_predicate(backoff.expo, max_time=3600)(self.has_completed_sync)(
            connector
        )

    def reload_schemas(self, connector: Connector) -> List[FivetranSchema]:

        # https://fivetran.com/docs/rest-api/connectors#reloadaconnectorschemaconfig

        res = requests.post(
            f"{settings.FIVETRAN_URL}/connectors/{connector.fivetran_id}/schemas/reload",
            headers=settings.FIVETRAN_HEADERS,
        ).json()

        if res["code"] != "Success":
            raise FivetranClientError()

        return _schemas_to_obj(res["data"].get("schemas", {}))

    def get_schemas(self, connector: Connector):

        # https://fivetran.com/docs/rest-api/connectors#retrieveaconnectorschemaconfig

        res = requests.get(
            f"{settings.FIVETRAN_URL}/connectors/{connector.fivetran_id}/schemas",
            headers=settings.FIVETRAN_HEADERS,
        ).json()

        # try a reload in case this connector is new
        if res["code"] == "NotFound_SchemaConfig":
            return self.reload_schemas(connector)

        if res["code"] != "Success":
            raise FivetranClientError()

        # schema not included for Google Sheets connector
        return _schemas_to_obj(res["data"].get("schemas", {}))

    def update_schemas(self, connector: Connector, schemas: List[FivetranSchema]):

        # https://fivetran.com/docs/rest-api/connectors#modifyaconnectorschemaconfig

        res = requests.patch(
            f"{settings.FIVETRAN_URL}/connectors/{connector.fivetran_id}/schemas",
            json={"schemas": _schemas_to_dict(schemas)},
            headers=settings.FIVETRAN_HEADERS,
        ).json()

        if res["code"] != "Success":
            raise FivetranClientError()

    def delete(self, connector: Connector):

        # we don't want to accidentally delete these fixtures used in local development
        if connector.fivetran_id in get_fixture_fivetran_ids():
            return

        res = requests.delete(
            f"{settings.FIVETRAN_URL}/connectors/{connector.fivetran_id}",
            headers=settings.FIVETRAN_HEADERS,
        ).json()

        if res["code"] != "Success":
            raise FivetranClientError()


MOCK_SCHEMA_DIR = os.path.abspath(".mock/.schema")


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

    def create(self, service, team_id):
        # duplicate the content of the first created existing connector
        connector = (
            Connector.objects.filter(service=service).order_by("id").first()
            or Connector.objects.filter(service=self.DEFAULT_SERVICE).first()
        )
        return {"fivetran_id": connector.fivetran_id, "schema": connector.schema}

    def start_initial_sync(self, connector):
        self._started[connector.id] = timezone.now()

    def start_update_sync(self, connector):
        self._started[connector.id] = timezone.now()

    def authorize(self, connector, redirect_uri):
        return redirect(f"{reverse('connectors:mock')}?redirect_uri={redirect_uri}")

    def has_completed_sync(self, connector):
        return (
            timezone.now() - self._started.get(connector.id, timezone.now())
        ).total_seconds() > self.REFRESH_SYNC_SECONDS

    def block_until_synced(self, connector):
        time.sleep(self.BLOCK_SYNC_SECONDS)

    def reload_schemas(self, connector):
        pass

    def get_schemas(self, connector):
        if connector.id in self._schema_cache:
            return _schemas_to_obj(self._schema_cache[connector.id])

        service = connector.service if connector is not None else "google_analytics"
        fivetran_id = connector.fivetran_id if connector is not None else "humid_rifle"

        with open(f"cypress/fixtures/fivetran/{service}_{fivetran_id}.json", "r") as f:
            return _schemas_to_obj(json.load(f))

    def update_schemas(self, connector, schemas):
        self._schema_cache[connector.id] = _schemas_to_dict(schemas)

    def delete(self, connector):
        pass


if settings.MOCK_FIVETRAN:
    FivetranClient = MockFivetranClient
