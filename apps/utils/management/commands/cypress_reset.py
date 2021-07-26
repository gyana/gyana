from apps.utils.test import create_testdb_from_template
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Reset the database to the template."

    def handle(self, *args, **options):

        create_testdb_from_template()
