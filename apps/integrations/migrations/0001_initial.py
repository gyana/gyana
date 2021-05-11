# Generated by Django 3.2 on 2021-05-10 23:39

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('projects', '0002_project_team'),
    ]

    operations = [
        migrations.CreateModel(
            name='Integration',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('kind', models.CharField(choices=[('google_sheets', 'Google Sheets'), ('csv', 'CSV'), ('fivetran', 'Fivetran')], max_length=32)),
                ('url', models.URLField(null=True)),
                ('file', models.FileField(null=True, upload_to='integrations')),
                ('has_initial_sync', models.BooleanField(default=False)),
                ('last_synced', models.DateTimeField(null=True)),
                ('service', models.TextField(max_length=255, null=True)),
                ('fivetran_id', models.TextField(null=True)),
                ('schema', models.TextField(null=True)),
                ('fivetran_authorized', models.BooleanField(default=False)),
                ('fivetran_poll_historical_sync_task_id', models.UUIDField(null=True)),
                ('historical_sync_complete', models.BooleanField(default=False)),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('project', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='projects.project')),
            ],
            options={
                'ordering': ('-created',),
            },
        ),
    ]
