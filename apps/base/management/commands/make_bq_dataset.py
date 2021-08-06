from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils.text import slugify
from google.cloud.exceptions import NotFound
from apps.base.clients import DATAFLOW_ID, DATASET_ID, bigquery_client


class Command(BaseCommand):
    help = "Creates a BigQuery dataset with the slugified CLOUD_NAMESPACE"

    def handle(self, *args, **options):
        client = bigquery_client()

        # Try and create a dataset using the {SLUG}_integrations name
        try:
            client.get_dataset(DATASET_ID)
            self.stdout.write(
                self.style.WARNING(
                    f"BigQuery dataset with slug '{DATASET_ID}' already exists"
                )
            )
        except NotFound:
            client.create_dataset(DATASET_ID)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully created BigQuery dataset with slug '{DATASET_ID}'"
                )
            )

        # Try and create a dataset using the {SLUG}_dataflows name
        try:
            client.get_dataset(DATAFLOW_ID)
            self.stdout.write(
                self.style.WARNING(
                    f"BigQuery dataset with slug '{DATAFLOW_ID}' already exists"
                )
            )
        except NotFound:
            client.create_dataset(DATAFLOW_ID)
            self.stdout.write(
                self.style.SUCCESS(
                    f"Successfully created BigQuery dataset with slug '{DATAFLOW_ID}'"
                )
            )

        self.stdout.write(self.style.SUCCESS(f"✨ Done"))
