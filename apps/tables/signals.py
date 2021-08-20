from django.db.models.signals import post_delete
from django.dispatch.dispatcher import receiver
from google.api_core.exceptions import NotFound

from apps.base.clients import bigquery_client

from .models import Table


@receiver(post_delete, sender=Table)
def delete_img_pre_delete_post(sender, instance, *args, **kwargs):
    try:
        bigquery_client().delete_table(instance.bq_obj)
    except (NotFound):
        pass
