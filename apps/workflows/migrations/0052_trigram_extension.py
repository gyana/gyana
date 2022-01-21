from django.db import migrations
from django.contrib.postgres.operations import TrigramExtension


class Migration(migrations.Migration):

    dependencies = [
        ('workflows', '0051_alter_workflow_state'),
    ]

    operations = [
        TrigramExtension(),
    ]
