# Generated by Django 3.2.13 on 2022-05-16 13:35

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('widgets', '0058_auto_20220516_1259'),
    ]

    operations = [
        migrations.AddField(
            model_name='historicalwidget',
            name='table_paginate_by',
            field=models.PositiveIntegerField(default=15, validators=[django.core.validators.MaxValueValidator(100)], verbose_name='Rows per page'),
        ),
        migrations.AddField(
            model_name='widget',
            name='table_paginate_by',
            field=models.PositiveIntegerField(default=15, validators=[django.core.validators.MaxValueValidator(100)], verbose_name='Rows per page'),
        ),
    ]
