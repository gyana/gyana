import analytics
from celery.app import shared_task
from django.conf import settings
from django.utils import timezone

from apps.base.analytics import EXPORT_CREATED
from apps.exports.emails import send_export_email
from apps.nodes.bigquery import get_query_from_node
from apps.tables.bigquery import get_query_from_table
from apps.users.models import CustomUser

from .bigquery import query_to_gcs
from .models import Export


@shared_task
def export_to_gcs(export_id, user_id):
    export = Export.objects.get(pk=export_id)
    user = CustomUser.objects.get(pk=user_id)

    if export.node:
        query = get_query_from_node(export.node)
    else:
        query = get_query_from_table(export.integration_table)

    query_to_gcs(query.compile(), f"gs://{settings.GS_BUCKET_NAME}/{export.path}")

    send_export_email(export.path, user)

    export.exported_at = timezone.now()
    export.save()

    analytics.track(
        user.id,
        EXPORT_CREATED,
        {
            "id": export.id,
        },
    )
