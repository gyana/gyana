import os

from celery import Celery, signature
from celery.schedules import crontab

# set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "gyana.settings.development")

app = Celery("gyana")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django app configs.
app.autodiscover_tasks()


@app.on_after_finalize.connect
def setup_periodic_tasks(sender, **kwargs):
    sender.add_periodic_task(
        # every 6 hours from midnight
        crontab(minute=0, hour="*/6"),
        signature("apps.integrations.tasks.delete_outdated_pending_integrations"),
    )
    sender.add_periodic_task(
        # every 6 hours from midnight
        crontab(minute=0, hour="*/6"),
        signature("apps.teams.tasks.update_team_row_limits"),
    )
    sender.add_periodic_task(
        # every ten minutes
        crontab(minute="*/10"),
        signature("apps.connectors.tasks.update_connectors_from_fivetran"),
    )
