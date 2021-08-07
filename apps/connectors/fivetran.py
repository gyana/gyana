import json
import time
import uuid

import backoff
import requests
from django.conf import settings
from django.shortcuts import redirect

from .utils import get_services


class FivetranClient:
    def create(self, service, team_id):

        service_conf = get_services()[service]

        schema = f"team_{team_id}_{service}_{uuid.uuid4().hex}"

        config = {"schema": schema, **(service_conf["static_config"] or {})}
        if service_conf["requires_schema_prefix"] == "t":
            config["schema_prefix"] = schema + "_"

        res = requests.post(
            f"{settings.FIVETRAN_URL}/connectors",
            json={
                "service": service,
                "group_id": settings.FIVETRAN_GROUP,
                "run_setup_tests": False,
                "paused": True,
                "config": config,
            },
            headers=settings.FIVETRAN_HEADERS,
        ).json()

        if res["code"] != "Success":
            # TODO
            pass

        return {"fivetran_id": res["data"]["id"], "schema": schema}

    def start(self, fivetran_id):
        res = requests.patch(
            f"{settings.FIVETRAN_URL}/connectors/{fivetran_id}",
            json={
                "paused": False,
            },
            headers=settings.FIVETRAN_HEADERS,
        ).json()

        if res["code"] != "Success":
            # TODO
            pass

        return res

    def authorize(self, fivetran_id, redirect_uri):

        card = requests.post(
            f"{settings.FIVETRAN_URL}/connectors/{fivetran_id}/connect-card-token",
            headers=settings.FIVETRAN_HEADERS,
        )
        connect_card_token = card.json()["token"]

        return redirect(
            f"https://fivetran.com/connect-card/setup?redirect_uri={redirect_uri}&auth={connect_card_token}"
        )

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
        """Gets all the tables of a connector"""
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

    def update_schema(self, fivetran_id, updated_checkboxes):
        """
        Transforms an array of schema and schema-table combinations to the correct Fivetran
        format. When checkboxes are unticked they're excluded and therefore assumed to be
        disabled. We create an initial structure with all schema and schema-table combinations
        set to false and the overlap with `updated_checkboxes` becomes enabled.

        Updating the schema relies on `updated_checkboxes` to be in an array with entries
        in the format of `{schema}` or `{schema}.{table}`.

        Refer to `connectors/_schema.html` for an example of the structure.
        """
        schema = self.get_schema(fivetran_id)

        # Construct a dictionary with all allowed schema changes and set them to false
        # By default when checkboxes are checked they are sent in a post request, if they
        # are unchecked they will be omitted from the POST data.
        update = {
            key: {
                "enabled": False,
                "tables": {
                    table: {"enabled": False}
                    for table, table_content in value["tables"].items()
                    if table_content["enabled_patch_settings"]["allowed"]
                },
            }
            for key, value in schema.items()
        }

        # Loop over our post data and update the changed schemas and tables values
        for key in updated_checkboxes:
            if len(ids := key.split(".")) > 1:
                schema, table = ids
                update[schema]["tables"][table] = {"enabled": True}
            else:
                update[key]["enabled"] = True

        res = requests.patch(
            f"{settings.FIVETRAN_URL}/connectors/{fivetran_id}/schemas",
            json={"schemas": update},
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
    def create(self, service, team_id):
        return {
            "fivetran_id": settings.MOCK_FIVETRAN_ID,
            "schema": settings.MOCK_FIVETRAN_SCHEMA,
        }

    def start(self, fivetran_id):
        pass

    def authorize(self, fivetran_id, redirect_uri):
        return redirect(redirect_uri)

    def block_until_synced(self, integration):
        time.sleep(settings.MOCK_FIVETRAN_HISTORICAL_SYNC_SECONDS)
        integration.connector.historical_sync_complete = True
        integration.save()

    def get_schema(self, fivetran_id):
        with open("cypress/fixtures/google_analytics_schema.json", "r") as f:
            return json.load(f)

    def update_schema(self, fivetran_id, updated_checkboxes):
        pass

    def update_table_config(self, fivetran_id, schema, table_name: str, enabled: bool):
        pass


if settings.MOCK_FIVETRAN:
    FivetranClient = MockFivetranClient
