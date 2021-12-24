# Generated by Django 3.2.7 on 2021-12-21 00:05

from django.db import migrations, models
import django_cryptography.fields


class Migration(migrations.Migration):

    dependencies = [
        ('customapis', '0010_alter_customapi_url'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customapi',
            name='api_key_value',
            field=django_cryptography.fields.encrypt(models.CharField(max_length=8192, null=True)),
        ),
        migrations.AlterField(
            model_name='customapi',
            name='bearer_token',
            field=django_cryptography.fields.encrypt(models.CharField(max_length=1024, null=True)),
        ),
        migrations.AlterField(
            model_name='customapi',
            name='password',
            field=django_cryptography.fields.encrypt(models.CharField(max_length=1024, null=True)),
        ),
    ]
