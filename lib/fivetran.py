import time
from dataclasses import dataclass
from functools import lru_cache
from uuid import uuid4

import backoff
import requests
import yaml
from apps.connectors.models import Connector
from django.conf import settings
from django.shortcuts import redirect

SERVICES = "lib/services.yaml"


@lru_cache
def get_services():
    return yaml.load(open(SERVICES, "r"))


@dataclass
class MockFivetranClient:

    connector: Connector

    def create(self):
        self.connector.fivetran_id = settings.MOCK_FIVETRAN_ID
        self.connector.schema = settings.MOCK_FIVETRAN_SCHEMA
        self.connector.save()

    def authorize(self, redirect_uri):
        return redirect(redirect_uri)

    def block_until_synced(self):
        time.sleep(settings.MOCK_FIVETRAN_HISTORICAL_SYNC_SECONDS)
        self.connector.historical_sync_complete = True
        self.connector.save()


@dataclass
class FivetranClient:

    connector: Connector

    def create(self):

        service = self.connector.service
        service_conf = get_services()[service]

        schema = f"{service}_{str(uuid4()).replace('-', '_')}"

        res = requests.post(
            f"{settings.FIVETRAN_URL}/connectors",
            json={
                "service": service,
                "group_id": settings.FIVETRAN_GROUP,
                # "run_setup_tests": False,
                "config": {"schema": schema, **service_conf["static_config"]},
            },
            headers=settings.FIVETRAN_HEADERS,
        ).json()

        if res["code"] != "Success":
            # TODO
            pass

        self.connector.fivetran_id = res["data"]["id"]
        self.connector.schema = schema
        self.connector.save()

    def authorize(self, redirect_uri):

        card = requests.post(
            f"{settings.FIVETRAN_URL}/connectors/{self.connector.fivetran_id}/connect-card-token",
            headers=settings.FIVETRAN_HEADERS,
        )
        connect_card_token = card.json()["token"]

        return redirect(
            f"https://fivetran.com/connect-card/setup?redirect_uri={redirect_uri}&auth={connect_card_token}&hide_setup_guide=true"
        )

    def _is_historical_synced(self):

        res = requests.get(
            f"{settings.FIVETRAN_URL}/connectors/{self.connector.fivetran_id}",
            headers=settings.FIVETRAN_HEADERS,
        ).json()

        if res["code"] != "Success":
            # TODO
            pass

        status = res["data"]["status"]

        return status["is_historical_sync"]

    def block_until_synced(self):

        backoff.on_predicate(backoff.expo, lambda x: x, max_time=3600)(
            self._is_historical_synced
        )()

        self.connector.historical_sync_complete = True
        self.connector.save()


if settings.MOCK_FIVETRAN:
    FivetranClient = MockFivetranClient
