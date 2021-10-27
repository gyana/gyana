import uuid
from typing import Dict, List

import backoff
import requests
from django.conf import settings

from ..models import Connector
from .config import get_services
from .schema import FivetranSchema, schemas_to_dict, schemas_to_obj

# wrapper for the Fivetran connectors REST API, documented here
# https://fivetran.com/docs/rest-api/connectors
# on error, raise a FivetranClientError and it will be managed in
# the caller (e.g. form) or trigger 500 (user can refresh/retry)


class FivetranClientError(Exception):
    def __init__(self, res) -> None:
        message = f'[Fivetran API Exception] {res["code"]}: {res["message"]}'
        super().__init__(message)


class FivetranClient:
    def create(self, service, team_id) -> Dict:
        from apps.base.clients import SLUG

        # https://fivetran.com/docs/rest-api/connectors#createaconnector

        service_conf = get_services()[service]

        config = service_conf.get("static_config", {})

        # https://fivetran.com/docs/rest-api/connectors/config
        # database connectors require schema_prefix, rather than schema

        schema = f"team_{team_id:06}_{service}_{uuid.uuid4().hex}"
        if SLUG:
            schema = f"{SLUG}_{schema}"

        config[
            "schema_prefix"
            if service_conf.get("requires_schema_prefix") == "t"
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
            raise FivetranClientError(res)

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

    def get(self, connector: Connector):

        # https://fivetran.com/docs/rest-api/connectors/connect-card#connectcard

        res = requests.get(
            f"{settings.FIVETRAN_URL}/connectors/{connector.fivetran_id}",
            headers=settings.FIVETRAN_HEADERS,
        ).json()

        if res["code"] != "Success":
            raise FivetranClientError(res)

        return res["data"]

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

    def has_completed_sync(self, connector: Connector) -> bool:

        res = requests.get(
            f"{settings.FIVETRAN_URL}/connectors/{connector.fivetran_id}",
            headers=settings.FIVETRAN_HEADERS,
        ).json()

        if res["code"] != "Success":
            raise FivetranClientError(res)

        status = res["data"]["status"]

        return not (status["is_historical_sync"] or status["sync_state"] == "syncing")

    def reload_schemas(self, connector: Connector) -> List[FivetranSchema]:

        # https://fivetran.com/docs/rest-api/connectors#reloadaconnectorschemaconfig

        res = requests.post(
            f"{settings.FIVETRAN_URL}/connectors/{connector.fivetran_id}/schemas/reload",
            headers=settings.FIVETRAN_HEADERS,
        ).json()

        if res["code"] != "Success":
            raise FivetranClientError(res)

        return schemas_to_obj(res["data"].get("schemas", {}))

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

        # schema not included for Google Sheets connector
        return schemas_to_obj(res["data"].get("schemas", {}))

    def update_schemas(self, connector: Connector, schemas: List[FivetranSchema]):

        # https://fivetran.com/docs/rest-api/connectors#modifyaconnectorschemaconfig

        res = requests.patch(
            f"{settings.FIVETRAN_URL}/connectors/{connector.fivetran_id}/schemas",
            json={"schemas": schemas_to_dict(schemas)},
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
