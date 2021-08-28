# Generated by Django 3.2.5 on 2021-08-24 21:30

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('teams', '0011_remove_team_enabled'),
    ]

    operations = [
        migrations.CreateModel(
            name='PurchasedCodes',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('data', models.FileField(upload_to='')),
                ('downloaded', models.DateTimeField()),
                ('success', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ('-created',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='RefundedCodes',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('data', models.FileField(upload_to='')),
                ('downloaded', models.DateTimeField()),
                ('success', models.BooleanField(default=False)),
            ],
            options={
                'ordering': ('-created',),
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='AppsumoCode',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('code', models.CharField(max_length=8, unique=True)),
                ('bought_before', models.DateTimeField(null=True)),
                ('redeemed', models.DateTimeField(null=True)),
                ('refunded_before', models.DateTimeField(null=True)),
                ('redeemed_by', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
                ('team', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='teams.team')),
            ],
            options={
                'ordering': ('-created',),
                'abstract': False,
            },
        ),
    ]
