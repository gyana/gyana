# Generated by Django 3.2.7 on 2021-12-06 21:39

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('schedules', '0002_schedule_run_task_id'),
    ]

    operations = [
        migrations.AddField(
            model_name='schedule',
            name='run_started_at',
            field=models.DateTimeField(null=True),
        ),
    ]
