import requests
import yaml
from apps.connectors.config import METADATA
from django.conf import settings
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Fetch the metadata for all Fivetran connectors"

    def handle(self, *args, **options):
        res = requests.get(
            f"{settings.FIVETRAN_URL}/metadata/connectors?limit=1000",
            headers=settings.FIVETRAN_HEADERS,
        ).json()

        if "next_cursor" in res["data"]:
            raise Exception("Fivetran fetched data is incomplete")

        # dump the metadata

        with open(METADATA, "w") as f:
            yaml.dump({r["id"]: r for r in res["data"]["items"]}, f)

        # download the images
