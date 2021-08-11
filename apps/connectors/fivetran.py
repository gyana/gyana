import json
import time
import uuid

import backoff
import requests
from apps.integrations.models import Integration
from django.conf import settings
from django.shortcuts import redirect
from django.urls.base import reverse

from .models import Connector
from .utils import get_services


class FivetranClient:
    def create(self, service, team_id):

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

    def authorize(self, fivetran_id, redirect_uri):

        card = requests.post(
            f"{settings.FIVETRAN_URL}/connectors/{fivetran_id}/connect-card-token",
            headers=settings.FIVETRAN_HEADERS,
        )
        connect_card_token = card.json()["token"]

        return redirect(
            f"https://fivetran.com/connect-card/setup?redirect_uri={redirect_uri}&auth={connect_card_token}"
        )

    def start(self, connector: Connector):

        res = requests.patch(
            f"{settings.FIVETRAN_URL}/connectors/{connector.fivetran_id}",
            json={
                "paused": False,
            },
            headers=settings.FIVETRAN_HEADERS,
        ).json()

        if res["code"] != "Success":
            # TODO
            pass

        return res

    def _is_historical_synced(self, fivetran_id):

        res = requests.get(
            f"{settings.FIVETRAN_URL}/connectors/{fivetran_id}",
            headers=settings.FIVETRAN_HEADERS,
        ).json()

        if res["code"] != "Success":
            # TODO
            pass

        status = res["data"]["status"]

        return status["is_historical_sync"]

    def block_until_synced(self, integration):

        backoff.on_predicate(backoff.expo, lambda x: x, max_time=3600)(
            self._is_historical_synced
        )(integration.connector.fivetran_id)

        integration.connector.historical_sync_complete = True
        integration.save()

    def get_schema(self, fivetran_id):

        # https://fivetran.com/docs/rest-api/connectors#retrieveaconnectorschemaconfig

        res = requests.get(
            f"{settings.FIVETRAN_URL}/connectors/{fivetran_id}/schemas",
            headers=settings.FIVETRAN_HEADERS,
        ).json()

        if res.get("code") == "NotFound_SchemaConfig":
            # First try a reload in case this connector is new
            # https://fivetran.com/docs/rest-api/connectors#reloadaconnectorschemaconfig
            res = requests.post(
                f"{settings.FIVETRAN_URL}/connectors/{fivetran_id}/schemas/reload",
                headers=settings.FIVETRAN_HEADERS,
            ).json()

        if res["code"] != "Success":
            # TODO
            pass

        return res["data"].get("schemas", {})

    def update_schema(self, fivetran_id, schemas):

        # https://fivetran.com/docs/rest-api/connectors#modifyaconnectorschemaconfig

        res = requests.patch(
            f"{settings.FIVETRAN_URL}/connectors/{fivetran_id}/schemas",
            json={"schemas": schemas},
            headers=settings.FIVETRAN_HEADERS,
        ).json()

        if res["code"] != "Success":
            # TODO
            pass

        return res

    def update_table_config(self, fivetran_id, schema, table_name: str, enabled: bool):
        res = requests.patch(
            f"{settings.FIVETRAN_URL}/connectors/{fivetran_id}/schemas/{schema}/tables/{table_name}",
            json={
                "enabled": enabled,
            },
            headers=settings.FIVETRAN_HEADERS,
        ).json()

        # Future note: If we write this to raise an error table deletion will stop working
        # for tables that fivetran won't allow to stop being synced. (This is on the TableDelete view)
        if res["code"] != "Success":
            # TODO
            pass

        return res


class MockFivetranClient:
    def __init__(self) -> None:
        self._schema_cache = {}

    def create(self, service, team_id):
        return {
            "success": True,
            "message": "Connector has been created",
            "data": {
                "fivetran_id": settings.MOCK_FIVETRAN_ID,
                "schema": settings.MOCK_FIVETRAN_SCHEMA,
            },
        }

    def start(self, fivetran_id):
        pass

    def authorize(self, fivetran_id, redirect_uri):
        return redirect(f"{reverse('connectors:mock')}?redirect_uri={redirect_uri}")

    def block_until_synced(self, integration):
        time.sleep(settings.MOCK_FIVETRAN_HISTORICAL_SYNC_SECONDS)
        integration.connector.historical_sync_complete = True
        integration.save()

    def get_schema(self, fivetran_id):
        if fivetran_id in self._schema_cache:
            return self._schema_cache[fivetran_id]

        connector = Connector.objects.filter(fivetran_id=fivetran_id).first()
        service = connector.service if connector is not None else "google_analytics"

        with open(f"cypress/fixtures/fivetran/{service}_schema.json", "r") as f:
            return json.load(f)

    def update_schema(self, fivetran_id, schemas):
        self._schema_cache[fivetran_id] = schemas

    def update_table_config(self, fivetran_id, schema, table_name: str, enabled: bool):
        pass


if settings.MOCK_FIVETRAN:
    FivetranClient = MockFivetranClient
