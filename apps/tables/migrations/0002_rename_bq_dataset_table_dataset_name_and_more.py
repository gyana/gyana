# Generated by Django 4.0.8 on 2024-01-20 10:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('tables', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='table',
            old_name='bq_dataset',
            new_name='dataset_name',
        ),
        migrations.RenameField(
            model_name='table',
            old_name='bq_table',
            new_name='table_name',
        ),
        migrations.AlterUniqueTogether(
            name='table',
            unique_together={('table_name', 'dataset_name')},
        ),
    ]
