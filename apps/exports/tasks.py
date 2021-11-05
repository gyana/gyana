from datetime import datetime as dt

from apps.base import clients
from apps.nodes.bigquery import get_query_from_node
from apps.tables.models import Table
from django.conf import settings
from django.core.mail.message import EmailMessage
from django.db import transaction
from google.cloud import bigquery

from .models import Export


def export_to_gcs(export, user):
    # export = Export.objects.get(pk=export_id)
    node = export.node

    with transaction.atomic():
        table = Table(
            source=Table.Source.EXPORT,
            bq_table=export.bq_table_id,
            bq_dataset=node.workflow.project.team.tables_dataset_id,
            project=node.workflow.project,
            export=export,
        )
        table.save()
        query = get_query_from_node(export.node)
        client = clients.bigquery()
        job_config = bigquery.QueryJobConfig(
            destination=f"{settings.GCP_PROJECT}.{table.bq_id}"
        )
        job = client.query(query.compile(), job_config=job_config)
        job.result()
        export.status = Export.Status.BQ_TABLE_CREATED
        export.save()

    gcs_path = f"{settings.GS_BUCKET_NAME}/exports/{export.bq_table_id}-{dt.now().isoformat()}.csv"
    extract_job = client.extract_table(table.bq_id, f"gs://{gcs_path}")
    extract_job.result()
    with transaction.atomic():
        export.gcs_path = gcs_path
        export.status = Export.Status.EXPORTED
        export.save()

    message = EmailMessage(
        subject="Your export is ready",
        body=f"Click the link to download <a href='https://storage.cloud.google.com/{gcs_path}'>download</a>.",
        from_email="Gyana Notifications <notifications@gyana.com>",
        to=[user.email],
    )
    message.send()
