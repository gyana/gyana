from apps.integrations.models import Integration
from apps.tables.models import Table
from apps.utils.clients import DATASET_ID, bigquery_client
from django.conf import settings
from django.core.management.base import BaseCommand
from google.cloud.exceptions import NotFound


class Command(BaseCommand):
    help = "Creates a BigQuery dataset with the slugified CLOUD_NAMESPACE"

    def handle(self, *args, **options):
        client = bigquery_client()

        # sheets and CSVs

        integration_table_pks = [
            int(t.table_id.lstrip("table_"))
            for t in client.list_tables(f"{settings.GCP_PROJECT}.{DATASET_ID}")
            if "external" not in t.table_id
        ]

        orphaned_csv = (
            Integration.objects.filter(kind=Integration.Kind.CSV)
            .exclude(table__pk__in=integration_table_pks)
            .all()
        )

        orphaned_google_sheet = (
            Integration.objects.filter(kind=Integration.Kind.GOOGLE_SHEETS)
            .exclude(table__pk__in=integration_table_pks)
            .all()
        )

        print(
            "CSVs",
            len(orphaned_csv),
            Integration.objects.filter(kind=Integration.Kind.CSV).count(),
        )
        print(
            "Google Sheets",
            len(orphaned_google_sheet),
            Integration.objects.filter(kind=Integration.Kind.GOOGLE_SHEETS).count(),
        )

        # fivetran

        integration_dataset_pks = [
            int(d.dataset_id.split("_")[-1])
            for d in list(client.list_datasets(project=settings.GCP_PROJECT))
            if d.dataset_id.startswith("team_")
            and d.dataset_id.split("_")[-1].isdigit()
        ]

        orphaned_fivetran = (
            Integration.objects.filter(kind=Integration.Kind.FIVETRAN)
            .exclude(table__pk__in=integration_dataset_pks)
            .all()
        )

        print(
            "Fivetran",
            len(orphaned_fivetran),
            Integration.objects.filter(kind=Integration.Kind.FIVETRAN).count(),
        )
