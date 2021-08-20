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
        # run at midnight UTC every day
        crontab(minute=0, hour=0),
        signature("apps.integrations.delete_outdated_pending_integrations"),
    )
    sender.add_periodic_task(
        # run at midnight UTC every day
        crontab(minute=0, hour=0),
        signature("apps.teams.update_team_row_limits"),
    )
