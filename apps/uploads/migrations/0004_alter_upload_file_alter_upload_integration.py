# Generated by Django 4.0.8 on 2024-03-19 22:14

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('integrations', '0003_alter_integration_kind'),
        ('uploads', '0003_alter_upload_file_gcs_path'),
    ]

    operations = [
        migrations.AlterField(
            model_name='upload',
            name='file',
            field=models.FileField(blank=True, null=True, upload_to='cypress-v2/integrations'),
        ),
        migrations.AlterField(
            model_name='upload',
            name='integration',
            field=models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='integrations.integration'),
        ),
    ]
