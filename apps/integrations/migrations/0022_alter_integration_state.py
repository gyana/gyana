# Generated by Django 3.2.7 on 2021-12-14 23:21

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('integrations', '0021_auto_20211207_2320'),
    ]

    operations = [
        migrations.AlterField(
            model_name='integration',
            name='state',
            field=models.CharField(choices=[('update', 'Update'), ('pending', 'Pending'), ('load', 'Load'), ('error', 'Error'), ('done', 'Done')], default='update', max_length=16),
        ),
    ]
