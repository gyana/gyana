import os

import requests
import yaml
from django.conf import settings
from django.core.management.base import BaseCommand

from apps.connectors.fivetran.config import METADATA

STATIC = "apps/integrations/static/images/integrations/fivetran"


class Command(BaseCommand):
    help = "Fetch the metadata for all Fivetran connectors."

    def handle(self, *args, **options):
        print("Downloading metadata...")
        res = requests.get(
            f"{settings.FIVETRAN_URL}/metadata/connectors?limit=1000",
            headers=settings.FIVETRAN_HEADERS,
        ).json()

        if "next_cursor" in res["data"]:
            raise Exception("Fivetran fetched data is incomplete")

        metadata = {r["id"]: r for r in res["data"]["items"]}

        # download the images

        for item in metadata.values():
            print("Downloading image for", item["id"], "...")

            id_ = item["id"]
            res = requests.get(item["icon_url"])

            _, ext = os.path.splitext(item["icon_url"])

            icon_path = f"{id_}{ext}"

            with open(f"{STATIC}/{icon_path}", "wb") as f:
                f.write(res.content)

            metadata[id_]["icon_path"] = icon_path

        # dump the metadata

        with open(METADATA, "w") as f:
            yaml.dump(metadata, f)

        print("...done.")
