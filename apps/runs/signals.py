from django.db.models.signals import post_save
from django.dispatch.dispatcher import receiver
from django_celery_results.models import TaskResult

from .models import Run


@receiver(post_save, sender=TaskResult)
def update_workflow_on_node_deletion(sender, instance, *args, **kwargs):
    run = Run.objects.filter(task_id=instance.task_id).first()

    if run:
        run.result = instance
        run.save()
