from django.db.models.signals import post_delete
from django.dispatch.dispatcher import receiver

from apps.base.clients import fivetran_client

from .models import Connector


@receiver(post_delete, sender=Connector)
def delete_fivetran_connector(sender, instance, *args, **kwargs):
    fivetran_client().delete(instance)
