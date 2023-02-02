# Generated by Django 4.0.8 on 2023-02-02 22:41

import apps.base.clone
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('integrations', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Sheet',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('url', models.URLField()),
                ('sheet_name', models.CharField(blank=True, help_text='Select a specific sheet by submitting the tab name', max_length=50, null=True, verbose_name='Sheet selection')),
                ('cell_range', models.CharField(blank=True, help_text='Select a range of cells e.g. A2:D14', max_length=64, null=True)),
                ('drive_file_last_modified_at_sync', models.DateTimeField(null=True)),
                ('drive_modified_date', models.DateTimeField(null=True)),
                ('integration', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to='integrations.integration')),
            ],
            options={
                'ordering': ('-updated',),
                'abstract': False,
            },
            bases=(apps.base.clone.CloneMixin, models.Model),
        ),
    ]
