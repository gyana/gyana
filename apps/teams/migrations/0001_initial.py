# Generated by Django 4.0.8 on 2023-02-02 22:41

import apps.base.clone
import apps.teams.utils
import dirtyfields.dirtyfields
from django.db import migrations, models
import django.db.models.deletion
import django.utils.timezone
import storages.backends.gcloud
import timezone_field.fields


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('djpaddle', '0002_alter_subscription_subscriber'),
    ]

    operations = [
        migrations.CreateModel(
            name='CreditStatement',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('balance', models.IntegerField()),
                ('credits_used', models.IntegerField()),
                ('credits_received', models.IntegerField()),
            ],
            options={
                'ordering': ('-created',),
            },
        ),
        migrations.CreateModel(
            name='CreditTransaction',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('transaction_type', models.CharField(choices=[('decrease', 'Decrease'), ('increase', 'Increase')], max_length=10)),
                ('amount', models.IntegerField()),
            ],
            options={
                'ordering': ('-created',),
            },
        ),
        migrations.CreateModel(
            name='Flag',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='The human/computer readable name.', max_length=100, unique=True, verbose_name='Name')),
                ('everyone', models.BooleanField(blank=True, help_text='Flip this flag on (Yes) or off (No) for everyone, overriding all other settings. Leave as Unknown to use normally.', null=True, verbose_name='Everyone')),
                ('percent', models.DecimalField(blank=True, decimal_places=1, help_text='A number between 0.0 and 99.9 to indicate a percentage of users for whom this flag will be active.', max_digits=3, null=True, verbose_name='Percent')),
                ('testing', models.BooleanField(default=False, help_text='Allow this flag to be set for a session for user testing', verbose_name='Testing')),
                ('superusers', models.BooleanField(default=True, help_text='Flag always active for superusers?', verbose_name='Superusers')),
                ('staff', models.BooleanField(default=False, help_text='Flag always active for staff?', verbose_name='Staff')),
                ('authenticated', models.BooleanField(default=False, help_text='Flag always active for authenticated users?', verbose_name='Authenticated')),
                ('languages', models.TextField(blank=True, default='', help_text='Activate this flag for users with one of these languages (comma-separated list)', verbose_name='Languages')),
                ('rollout', models.BooleanField(default=False, help_text='Activate roll-out mode?', verbose_name='Rollout')),
                ('note', models.TextField(blank=True, help_text='Note where this Flag is used.', verbose_name='Note')),
                ('created', models.DateTimeField(db_index=True, default=django.utils.timezone.now, help_text='Date when this Flag was created.', verbose_name='Created')),
                ('modified', models.DateTimeField(default=django.utils.timezone.now, help_text='Date when this Flag was last modified.', verbose_name='Modified')),
            ],
            options={
                'verbose_name': 'Flag',
                'verbose_name_plural': 'Flags',
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Membership',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('role', models.CharField(choices=[('admin', 'Administrator'), ('member', 'Member')], max_length=100)),
            ],
            options={
                'ordering': ('-updated',),
                'abstract': False,
            },
            bases=(apps.base.clone.CloneMixin, models.Model),
        ),
        migrations.CreateModel(
            name='Team',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created', models.DateTimeField(auto_now_add=True)),
                ('updated', models.DateTimeField(auto_now=True)),
                ('deleted', models.DateTimeField(db_index=True, editable=False, null=True)),
                ('deleted_by_cascade', models.BooleanField(default=False, editable=False)),
                ('icon', models.FileField(blank=True, null=True, storage=storages.backends.gcloud.GoogleCloudStorage(bucket_name='gyana-local-public', cache_control='public, max-age=31536000', querystring_auth=False), upload_to='team-icons/')),
                ('color', models.CharField(default=apps.teams.utils.getRandomColor, max_length=7)),
                ('name', models.CharField(max_length=100)),
                ('override_row_limit', models.BigIntegerField(blank=True, null=True)),
                ('override_credit_limit', models.BigIntegerField(blank=True, null=True)),
                ('override_rows_per_integration_limit', models.BigIntegerField(blank=True, null=True)),
                ('row_count', models.BigIntegerField(default=0)),
                ('row_count_calculated', models.DateTimeField(null=True)),
                ('timezone', timezone_field.fields.TimeZoneField(choices_display='WITH_GMT_OFFSET', default='GMT')),
                ('has_free_trial', models.BooleanField(default=False)),
                ('last_checkout', models.OneToOneField(null=True, on_delete=django.db.models.deletion.SET_NULL, to='djpaddle.checkout')),
            ],
            options={
                'ordering': ('-created',),
            },
            bases=(dirtyfields.dirtyfields.DirtyFieldsMixin, apps.base.clone.CloneMixin, models.Model),
        ),
    ]
