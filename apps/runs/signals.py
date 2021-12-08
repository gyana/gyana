from django.db.models.signals import post_save
from django.dispatch.dispatcher import receiver
from django_celery_results.models import TaskResult

from .models import JobRun


@receiver(post_save, sender=TaskResult)
def update_run_on_task_result_save(sender, instance, *args, **kwargs):
    run = JobRun.objects.filter(task_id=instance.task_id).first()

    if run:
        if not run.result:
            run.result = instance
        run.update_run_from_result()
        run.save()
