# Generated by Django 3.2.5 on 2021-08-11 22:55

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('connectors', '0003_auto_20210811_1601'),
    ]

    operations = [
        migrations.RenameField(
            model_name='connector',
            old_name='fivetran_poll_historical_sync_task_id',
            new_name='sync_task_id',
        ),
        migrations.RemoveField(
            model_name='connector',
            name='historical_sync_complete',
        ),
        migrations.RemoveField(
            model_name='connector',
            name='last_synced',
        ),
        migrations.AddField(
            model_name='connector',
            name='sync_started',
            field=models.DateTimeField(null=True),
        ),
    ]
