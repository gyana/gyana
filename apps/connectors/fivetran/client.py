import uuid
from typing import Dict

import requests
from django.conf import settings

from ..models import Connector
from .config import ServiceTypeEnum, get_services_obj

# certain connectors (e.g. azure_sql_db) will block /schemas/reload for >2 mins
# before failing due to authentication error
RELOAD_SCHEMAS_TIMEOUT = 10

# wrapper for the Fivetran connectors REST API, documented here
# https://fivetran.com/docs/rest-api/connectors
# on error, raise a FivetranClientError and it will be managed in
# the caller (e.g. form) or trigger 500 (user can refresh/retry)


class FivetranClientError(Exception):
    def __init__(self, res) -> None:
        message = f'[Fivetran API Exception] {res["code"]}: {res["message"]}'
        super().__init__(message)


class FivetranClient:
    def create(self, service, team_id, daily_sync_time) -> Dict:
        from apps.base.clients import SLUG

        # https://fivetran.com/docs/rest-api/connectors#createaconnector

        service_conf = get_services_obj()[service]

        config = service_conf.static_config

        # https://fivetran.com/docs/rest-api/connectors/config
        # database connectors require schema_prefix, rather than schema

        schema = f"team_{team_id:06}_{service}_{uuid.uuid4().hex}"
        if SLUG:
            schema = f"{SLUG}_{schema}"

        config[
            "schema_prefix"
            if service_conf.service_type == ServiceTypeEnum.DATABASE
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
                "sync_frequency": 1440,
                "daily_sync_time": daily_sync_time,
                "config": config,
            },
            headers=settings.FIVETRAN_HEADERS,
        ).json()

        if res["code"] != "Success":
            raise FivetranClientError(res)

        return res["data"]

    def get(self, connector: Connector):

        # https://fivetran.com/docs/rest-api/connectors/connect-card#connectcard

        res = requests.get(
            f"{settings.FIVETRAN_URL}/connectors/{connector.fivetran_id}",
            headers=settings.FIVETRAN_HEADERS,
        ).json()

        if res["code"] != "Success":
            raise FivetranClientError(res)

        return res["data"]

    def list(self):
        session = requests.Session()
        url = f"{settings.FIVETRAN_URL}/groups/{settings.FIVETRAN_GROUP}/connectors"
        next_cursor = None

        while True:
            page = session.get(
                url,
                headers=settings.FIVETRAN_HEADERS,
                params={"limit": 100, "cursor": next_cursor},
            ).json()
            yield from page["data"]["items"]
            if (next_cursor := page["data"].get("next_cursor")) is None:
                break

    def update(self, connector: Connector, **data):

        # https://fivetran.com/docs/rest-api/connectors#modifyaconnector

        res = requests.patch(
            f"{settings.FIVETRAN_URL}/connectors/{connector.fivetran_id}",
            json=data,
            headers=settings.FIVETRAN_HEADERS,
        ).json()

        if res["code"] != "Success":
            raise FivetranClientError(res)

        return res

    def test(self, connector: Connector):

        # https://fivetran.com/docs/rest-api/connectors#runconnectorsetuptests

        res = requests.post(
            f"{settings.FIVETRAN_URL}/connectors/{connector.fivetran_id}/test",
            json={},
            headers=settings.FIVETRAN_HEADERS,
        ).json()

        if res["code"] != "Success":
            raise FivetranClientError(res)

    def get_authorize_url(self, connector: Connector, redirect_uri: str) -> str:

        # https://fivetran.com/docs/rest-api/connectors/connect-card#connectcard

        card = requests.post(
            f"{settings.FIVETRAN_URL}/connectors/{connector.fivetran_id}/connect-card-token",
            headers=settings.FIVETRAN_HEADERS,
        )
        connect_card_token = card.json()["token"]

        return f"https://fivetran.com/connect-card/setup?redirect_uri={redirect_uri}&auth={connect_card_token}"

    def start_initial_sync(self, connector: Connector) -> Dict:

        # https://fivetran.com/docs/rest-api/connectors#modifyaconnector

        res = requests.patch(
            f"{settings.FIVETRAN_URL}/connectors/{connector.fivetran_id}",
            json={"paused": False},
            headers=settings.FIVETRAN_HEADERS,
        ).json()

        if res["code"] != "Success":
            raise FivetranClientError(res)

        return res

    def start_update_sync(self, connector: Connector) -> Dict:

        # https://fivetran.com/docs/rest-api/connectors#syncconnectordata

        res = requests.post(
            f"{settings.FIVETRAN_URL}/connectors/{connector.fivetran_id}/force",
            headers=settings.FIVETRAN_HEADERS,
        ).json()

        if res["code"] != "Success":
            raise FivetranClientError(res)

        return res

    def reload_schemas(self, connector: Connector):

        # https://fivetran.com/docs/rest-api/connectors#reloadaconnectorschemaconfig

        res = requests.post(
            f"{settings.FIVETRAN_URL}/connectors/{connector.fivetran_id}/schemas/reload",
            headers=settings.FIVETRAN_HEADERS,
            timeout=RELOAD_SCHEMAS_TIMEOUT,
        ).json()

        if res["code"] != "Success":
            raise FivetranClientError(res)

        return res["data"].get("schemas", {})

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
            raise FivetranClientError(res)

        # schema not included for certain connector (e.g. sheets)
        return res["data"].get("schemas", {})

    def update_schemas(self, connector: Connector, schemas):

        # https://fivetran.com/docs/rest-api/connectors#modifyaconnectorschemaconfig

        res = requests.patch(
            f"{settings.FIVETRAN_URL}/connectors/{connector.fivetran_id}/schemas",
            json={"schemas": schemas},
            headers=settings.FIVETRAN_HEADERS,
        ).json()

        if res["code"] != "Success":
            raise FivetranClientError(res)

    def delete(self, connector: Connector):

        from .mock import get_fixture_fivetran_ids

        # we don't want to accidentally delete these fixtures used in local development
        if connector.fivetran_id in get_fixture_fivetran_ids():
            return

        res = requests.delete(
            f"{settings.FIVETRAN_URL}/connectors/{connector.fivetran_id}",
            headers=settings.FIVETRAN_HEADERS,
        ).json()

        if res["code"] != "Success":
            raise FivetranClientError(res)


if settings.MOCK_FIVETRAN:
    from .mock import MockFivetranClient

    FivetranClient = MockFivetranClient
