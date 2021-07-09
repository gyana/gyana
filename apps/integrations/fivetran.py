import time
from dataclasses import dataclass
from functools import lru_cache

import backoff
import requests
import yaml
from apps.integrations.models import Integration
from django.conf import settings
from django.shortcuts import redirect

SERVICES = "lib/services.yaml"


@lru_cache
def get_services():
    return {
        key: val
        for key, val in yaml.load(open(SERVICES, "r")).items()
        if val["internal"] != "t"
    }


@lru_cache
def get_service_categories():
    services = get_services()
    service_categories = []

    for service in services:
        if services[service]["category"] not in service_categories:
            service_categories.append(services[service]["category"])

    return service_categories


@dataclass
class MockFivetranClient:

    integration: Integration

    def create(self):
        self.integration.fivetran_id = settings.MOCK_FIVETRAN_ID
        self.integration.schema = settings.MOCK_FIVETRAN_SCHEMA
        self.integration.save()

    def authorize(self, redirect_uri):
        return redirect(redirect_uri)

    def block_until_synced(self):
        time.sleep(settings.MOCK_FIVETRAN_HISTORICAL_SYNC_SECONDS)
        self.integration.historical_sync_complete = True
        self.integration.save()


@dataclass
class FivetranClient:

    integration: Integration

    def create(self):

        service = self.integration.service
        service_conf = get_services()[service]

        schema = (
            f"team_{self.integration.project.team.pk}_{service}_{self.integration.pk}"
        )

        config = {"schema": schema, **(service_conf["static_config"] or {})}
        if service_conf["requires_schema_prefix"] == "t":
            config["schema_prefix"] = schema + "_"

        res = requests.post(
            f"{settings.FIVETRAN_URL}/connectors",
            json={
                "service": service,
                "group_id": settings.FIVETRAN_GROUP,
                "run_setup_tests": False,
                "config": config,
            },
            headers=settings.FIVETRAN_HEADERS,
        ).json()

        if res["code"] != "Success":
            # TODO
            pass

        self.integration.fivetran_id = res["data"]["id"]
        self.integration.schema = schema
        self.integration.save()

    def authorize(self, redirect_uri):

        card = requests.post(
            f"{settings.FIVETRAN_URL}/connectors/{self.integration.fivetran_id}/connect-card-token",
            headers=settings.FIVETRAN_HEADERS,
        )
        connect_card_token = card.json()["token"]

        return redirect(
            f"https://fivetran.com/connect-card/setup?redirect_uri={redirect_uri}&auth={connect_card_token}&hide_setup_guide=true"
        )

    def _is_historical_synced(self):

        res = requests.get(
            f"{settings.FIVETRAN_URL}/connectors/{self.integration.fivetran_id}",
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

        self.integration.historical_sync_complete = True
        self.integration.save()


if settings.MOCK_FIVETRAN:
    FivetranClient = MockFivetranClient
