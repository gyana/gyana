from django.db.models.signals import post_save
from django.dispatch.dispatcher import receiver
from django_celery_results.models import TaskResult

from .models import Run


@receiver(post_save, sender=TaskResult)
def update_run_on_task_result_save(sender, instance, *args, **kwargs):
    run = Run.objects.filter(task_id=instance.task_id).first()

    if run:
        run.result = instance
        run.save()


@receiver(post_save, sender=Run)
def update_integration_on_run_save(sender, instance, *args, **kwargs):
    if instance.source == Run.Source.INTEGRATION:
        instance.integration.update_state_from_latest_run()
