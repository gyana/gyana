# Generated by Django 3.2.12 on 2022-04-25 15:04

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('connectors', '0020_alter_connector_fivetran_id'),
    ]

    operations = [
        migrations.AlterField(
            model_name='connector',
            name='sync_state',
            field=models.CharField(choices=[('scheduled', 'Scheduled - the sync is waiting to be run'), ('syncing', 'Syncing - the sync is currently running'), ('paused', 'Paused - the sync is currently paused'), ('rescheduled', 'Rescheduled - the sync is waiting until more API calls are available in the source service'), ('sunset', "Sunset - this connector is no longer supported and won't sync.")], max_length=16),
        ),
    ]
