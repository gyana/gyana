# Generated by Django 3.2 on 2021-07-12 14:34

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('workflows', '0037_auto_20210712_0937'),
    ]

    operations = [
        migrations.AddField(
            model_name='workflow',
            name='data_updated',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
    ]
