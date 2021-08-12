import json
import time
import uuid

import backoff
import requests
from django.conf import settings
from django.shortcuts import redirect
from django.urls.base import reverse
from django.utils import timezone

from .config import get_services
from .models import Connector

# wrapper for the Fivetran connectors REST API, documented here
# https://fivetran.com/docs/rest-api/connectors
# on error, either raise an Exception (500 error) or explicitly
# return a success code to caller


class FivetranClient:
    def create(self, service, team_id):

        # https://fivetran.com/docs/rest-api/connectors#createaconnector

        service_conf = get_services()[service]

        config = service_conf["static_config"] or {}

        # https://fivetran.com/docs/rest-api/connectors/config
        # database connectors require schema_prefix, rather than schema

        schema = f"team_{team_id}_{service}_{uuid.uuid4().hex}"

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

        assert schema == res["data"]["schema"]

        # response schema https://fivetran.com/docs/rest-api/connectors#response_1
        #  {
        #   "code": "Success",
        #   "message": "Connector has been created",
        #   "data": {
        #       "id": "{{ fivetran_id }}",
        #       "schema": "{{ schema }}",
        #       ...
        #    }
        #  }
        return {
            "success": res["code"] == "Success",
            "message": res["message"],
            "data": {"fivetran_id": res["data"]["id"], "schema": res["data"]["schema"]},
        }

    def authorize(self, connector: Connector, redirect_uri):

        # https://fivetran.com/docs/rest-api/connectors/connect-card#connectcard

        card = requests.post(
            f"{settings.FIVETRAN_URL}/connectors/{connector.fivetran_id}/connect-card-token",
            headers=settings.FIVETRAN_HEADERS,
        )
        connect_card_token = card.json()["token"]

        return redirect(
            f"https://fivetran.com/connect-card/setup?redirect_uri={redirect_uri}&auth={connect_card_token}"
        )

    def start_initial_sync(self, connector: Connector):

        # https://fivetran.com/docs/rest-api/connectors#modifyaconnector

        res = requests.patch(
            f"{settings.FIVETRAN_URL}/connectors/{connector.fivetran_id}",
            json={"paused": False},
            headers=settings.FIVETRAN_HEADERS,
        ).json()

        if res["code"] != "Success":
            raise Exception()

        return res

    def start_update_sync(self, connector: Connector):

        # https://fivetran.com/docs/rest-api/connectors#syncconnectordata

        res = requests.post(
            f"{settings.FIVETRAN_URL}/connectors/{connector.fivetran_id}/force",
            headers=settings.FIVETRAN_HEADERS,
        ).json()

        if res["code"] != "Success":
            raise Exception()

        return res

    def has_completed_sync(self, connector):

        res = requests.get(
            f"{settings.FIVETRAN_URL}/connectors/{connector.fivetran_id}",
            headers=settings.FIVETRAN_HEADERS,
        ).json()

        if res["code"] != "Success":
            raise Exception()

        status = res["data"]["status"]

        return not (status["is_historical_sync"] or status["sync_state"] == "syncing")

    def block_until_synced(self, connector):

        backoff.on_predicate(backoff.expo, max_time=3600)(self.has_completed_sync)(
            connector
        )

    def reload_schema(self, connector):

        # https://fivetran.com/docs/rest-api/connectors#reloadaconnectorschemaconfig

        res = requests.post(
            f"{settings.FIVETRAN_URL}/connectors/{connector.fivetran_id}/schemas/reload",
            headers=settings.FIVETRAN_HEADERS,
        ).json()

        if res["code"] != "Success":
            raise Exception()

        return res["data"].get("schemas", {})

    def get_schema(self, connector):

        # https://fivetran.com/docs/rest-api/connectors#retrieveaconnectorschemaconfig

        res = requests.get(
            f"{settings.FIVETRAN_URL}/connectors/{connector.fivetran_id}/schemas",
            headers=settings.FIVETRAN_HEADERS,
        ).json()

        # try a reload in case this connector is new
        if res["code"] == "NotFound_SchemaConfig":
            return self.reload_schema(connector)

        if res["code"] != "Success":
            raise Exception()

        return res["data"].get("schemas", {})

    def update_schema(self, connector, schemas):

        # https://fivetran.com/docs/rest-api/connectors#modifyaconnectorschemaconfig

        res = requests.patch(
            f"{settings.FIVETRAN_URL}/connectors/{connector.fivetran_id}/schemas",
            json={"schemas": schemas},
            headers=settings.FIVETRAN_HEADERS,
        ).json()

        return res["code"] == "Success"


class MockFivetranClient:

    # default if not available in fixtures
    DEFAULT_SERVICE = "google_analytics"
    # wait 1s if refreshing page, otherwise 5 seconds for task to complete
    REFRESH_SYNC_SECONDS = 1
    BLOCK_SYNC_SECONDS = 5

    def __init__(self) -> None:
        self._schema_cache = {}
        self._started = {}

    def create(self, service, team_id):
        # duplicate the content of an existing connector
        connector = (
            Connector.objects.filter(service=service).first()
            or Connector.objects.filter(service=self.DEFAULT_SERVICE).first()
        )
        return {
            "success": True,
            "message": "Connector has been created",
            "data": {
                "fivetran_id": connector.fivetran_id,
                "schema": connector.schema,
            },
        }

    def start_initial_sync(self, connector):
        self._started[connector.id] = timezone.now()

    def start_update_sync(self, connector):
        self._started[connector.id] = timezone.now()

    def authorize(self, connector, redirect_uri):
        return redirect(f"{reverse('connectors:mock')}?redirect_uri={redirect_uri}")

    def has_completed_sync(self, connector):
        return (
            timezone.now() - self._started[connector.id]
        ).total_seconds() > self.REFRESH_SYNC_SECONDS

    def block_until_synced(self, connector):
        time.sleep(self.BLOCK_SYNC_SECONDS)

    def reload_schema(self, connector):
        pass

    def get_schema(self, connector):
        if connector.id in self._schema_cache:
            return self._schema_cache[connector.id]

        service = connector.service if connector is not None else "google_analytics"

        with open(f"cypress/fixtures/fivetran/{service}_schema.json", "r") as f:
            return json.load(f)

    def update_schema(self, connector, schemas):
        self._schema_cache[connector.id] = schemas


if settings.MOCK_FIVETRAN:
    FivetranClient = MockFivetranClient
