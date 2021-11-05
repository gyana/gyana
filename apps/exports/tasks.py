from datetime import datetime as dt
from datetime import timedelta

from apps.base import clients
from apps.base.utils import short_hash
from apps.nodes.bigquery import get_query_from_node
from apps.tables.models import Table
from apps.users.models import CustomUser
from celery.app import shared_task
from django.conf import settings
from django.core.mail.message import EmailMultiAlternatives
from django.db import transaction
from django.template import Context
from django.template.loader import get_template
from google.cloud import bigquery

from .models import Export


@shared_task
def export_to_gcs(export_id, user_id):
    export = Export.objects.get(pk=export_id)
    user = CustomUser.objects.get(pk=user_id)

    with transaction.atomic():
        query = get_query_from_node(export.node)
        client = clients.bigquery()

        job = client.query(query.compile())
        job.result()
        export.status = Export.Status.BQ_TABLE_CREATED
        export.save()

    filepath = f"exports/{export.table_id}-{short_hash()}.csv"
    gcs_path = f"{settings.GS_BUCKET_NAME}/{filepath}"
    extract_job = client.extract_table(job.destination, f"gs://{gcs_path}")
    extract_job.result()

    with transaction.atomic():
        export.gcs_path = gcs_path
        export.status = Export.Status.EXPORTED
        export.save()

    message_template_plain = get_template("exports/email/export_ready_message.txt")
    message_template = get_template("exports/email/export_ready_message.html")

    blob = clients.get_bucket().blob(filepath)
    url = blob.generate_signed_url(
        version="v4", expiration=dt.now() + timedelta(days=7)
    )
    message = EmailMultiAlternatives(
        "Your export is ready",
        message_template_plain.render({"user": user, "url": url}),
        "Gyana Notifications <notifications@gyana.com>",
        [user.email],
    )
    message.attach_alternative(
        message_template.render({"user": user, "url": url}), "text/html"
    )
    message.send()
