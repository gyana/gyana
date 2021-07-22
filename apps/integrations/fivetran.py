import time
from dataclasses import dataclass

import backoff
import requests
from apps.integrations.models import Integration
from apps.integrations.utils import get_services
from django.conf import settings
from django.shortcuts import redirect


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
                "paused": True,
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

    def start(self):
        res = requests.patch(
            f"{settings.FIVETRAN_URL}/connectors/{self.integration.fivetran_id}",
            json={
                "paused": False,
            },
            headers=settings.FIVETRAN_HEADERS,
        ).json()

        if res["code"] != "Success":
            # TODO
            pass

        return res

    def authorize(self, redirect_uri):

        card = requests.post(
            f"{settings.FIVETRAN_URL}/connectors/{self.integration.fivetran_id}/connect-card-token",
            headers=settings.FIVETRAN_HEADERS,
        )
        connect_card_token = card.json()["token"]

        return redirect(
            f"https://fivetran.com/connect-card/setup?redirect_uri={redirect_uri}&auth={connect_card_token}"
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

    def get_schema(self):
        res = requests.get(
            f"{settings.FIVETRAN_URL}/connectors/{self.integration.fivetran_id}/schemas",
            headers=settings.FIVETRAN_HEADERS,
        ).json()

        if res.get("code") == "NotFound_SchemaConfig":
            # First try a reload in case this connector is new
            # https://fivetran.com/docs/rest-api/connectors#reloadaconnectorschemaconfig
            res = requests.post(
                f"{settings.FIVETRAN_URL}/connectors/{self.integration.fivetran_id}/schemas/reload",
                headers=settings.FIVETRAN_HEADERS,
            ).json()

        if res["code"] != "Success":
            # TODO
            pass

        return res["data"].get("schemas", {})

    def update_schema(self, updated_checkboxes):
        """
        Transforms an array of schema and schema-table combinations to the correct Fivetran
        format. When checkboxes are unticked they're excluded and therefore assumed to be
        disabled. We create an initial structure with all schema and schema-table combinations
        set to false and the overlap with `updated_checkboxes` becomes enabled.

        Updating the schema relies on `updated_checkboxes` to be in an array with entries
        in the format of `{schema}` or `{schema}.{table}`.

        Refer to `integrations/_schema.html` for an example of the structure.
        """
        schema = self.get_schema()

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
            f"{settings.FIVETRAN_URL}/connectors/{self.integration.fivetran_id}/schemas",
            json={"schemas": update},
            headers=settings.FIVETRAN_HEADERS,
        ).json()

        if res["code"] != "Success":
            # TODO
            pass

        return res

    def update_table_config(self, table_name: str, enabled: bool):
        res = requests.patch(
            f"{settings.FIVETRAN_URL}/connectors/{self.integration.fivetran_id}/schemas/{self.integration.schema}/tables/{table_name}",
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


@dataclass
class MockFivetranClient(FivetranClient):
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


if settings.MOCK_FIVETRAN:
    FivetranClient = MockFivetranClient
