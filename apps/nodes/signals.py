from django.db.models.signals import post_delete
from django.dispatch.dispatcher import receiver
from django.utils import timezone

from .models import Edge, Node


@receiver(post_delete, sender=Node)
def update_workflow_on_node_deletion(sender, instance, *args, **kwargs):
    instance.workflow.data_updated = timezone.now()
    instance.workflow.save()


@receiver(post_delete, sender=Edge)
def update_workflow_on_edge_deletion(sender, instance, *args, **kwargs):
    instance.child.data_updated = timezone.now()
    instance.child.save()
