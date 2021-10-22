# Generated by Django 3.2.7 on 2021-10-22 10:14

from django.db import migrations, models
import storages.backends.gcloud


class Migration(migrations.Migration):

    dependencies = [
        ('teams', '0018_alter_team_options'),
    ]

    operations = [
        migrations.AlterField(
            model_name='team',
            name='icon',
            field=models.FileField(blank=True, null=True, storage=storages.backends.gcloud.GoogleCloudStorage(bucket_name='gyana-local-public', cache_control='public, max-age=31536000', querystring_auth=False), upload_to='team-icons/'),
        ),
    ]
