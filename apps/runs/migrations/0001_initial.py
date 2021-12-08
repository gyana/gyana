# Generated by Django 3.2.7 on 2021-12-08 14:06

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('integrations', '0020_alter_integration_options'),
        ('django_celery_results', '0010_remove_duplicate_indices'),
        ('workflows', '0045_auto_20211203_2239'),
    ]

    operations = [
        migrations.CreateModel(
            name='Run',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('state', models.CharField(choices=[('pending', 'Pending'), ('running', 'Running'), ('failed', 'Failed'), ('success', 'Success')], max_length=8)),
                ('done', models.DateTimeField(null=True)),
                ('task_id', models.UUIDField(null=True)),
                ('source', models.CharField(choices=[('integration', 'Integration'), ('workflow', 'Workflow')], max_length=16)),
                ('integration', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='integrations.integration')),
                ('result', models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, to='django_celery_results.taskresult')),
                ('workflow', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, to='workflows.workflow')),
            ],
            options={
                'ordering': ('-updated',),
                'abstract': False,
            },
        ),
    ]
