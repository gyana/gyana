# Generated by Django 3.2 on 2021-05-10 02:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('datasets', '0006_auto_20210505_0416'),
    ]

    operations = [
        migrations.AddField(
            model_name='dataset',
            name='fivetran_authorized',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='dataset',
            name='fivetran_id',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='dataset',
            name='fivetran_poll_historical_sync_task_id',
            field=models.UUIDField(null=True),
        ),
        migrations.AddField(
            model_name='dataset',
            name='historical_sync_complete',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='dataset',
            name='schema',
            field=models.TextField(null=True),
        ),
        migrations.AddField(
            model_name='dataset',
            name='service',
            field=models.TextField(default='google_sheets', max_length=255),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name='dataset',
            name='kind',
            field=models.CharField(choices=[('google_sheets', 'Google Sheets'), ('csv', 'CSV'), ('fivetran', 'Fivetran')], max_length=32),
        ),
    ]
