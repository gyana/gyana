from django.db.models.signals import post_save
from django.dispatch.dispatcher import receiver
from django_celery_results.models import TaskResult

from .models import GraphRun, JobRun


@receiver(post_save, sender=TaskResult)
def update_run_on_task_result_save(sender, instance, *args, **kwargs):
    job_run = JobRun.objects.filter(task_id=instance.task_id).first()
    graph_run = GraphRun.objects.filter(task_id=instance.task_id).first()

    if job_run:
        if not job_run.result:
            job_run.result = instance
        job_run.update_run_from_result()
        job_run.save()

    elif graph_run:
        if not graph_run.result:
            graph_run.result = instance
        graph_run.update_run_from_result()
        graph_run.save()
