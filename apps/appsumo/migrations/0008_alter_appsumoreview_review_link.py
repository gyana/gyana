# Generated by Django 3.2.6 on 2021-09-18 16:34

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('appsumo', '0007_auto_20210902_2305'),
    ]

    operations = [
        migrations.AlterField(
            model_name='appsumoreview',
            name='review_link',
            field=models.CharField(error_messages={'unique': "A user has linked to this review for their team. If you think this is a mistake, reach out to support and we'll sort it out for you."}, max_length=200, unique=True, validators=[django.core.validators.RegexValidator(message='Paste the exact link as displayed on AppSumo', regex='^https:\\/\\/appsumo\\.com\\/products\\/marketplace-gyana\\/\\#r[0-9]{6,9}$')]),
        ),
    ]
