# Generated by Django 3.2.7 on 2021-09-27 17:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('teams', '0017_auto_20210927_1423'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='team',
            name='max_credit',
        ),
    ]
