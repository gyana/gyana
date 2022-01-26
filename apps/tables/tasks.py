from celery import shared_task

from apps.base import clients


@shared_task
def copy_table(new_table, old_table):
    client = clients.bigquery()
    client.query(f"CREATE TABLE {new_table} as (SELECT * FROM {old_table})").result()
