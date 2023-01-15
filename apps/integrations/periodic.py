from celery.app import shared_task

from apps.base.tasks import honeybadger_check_in

from .models import Integration


@shared_task
def delete_outdated_pending_integrations():
    # will automatically delete associated bigquery entities
    Integration.objects.pending_should_be_deleted().delete()

    honeybadger_check_in("LoI4LK")
