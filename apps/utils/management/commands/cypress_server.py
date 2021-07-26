from apps.utils.test import create_template_from_testdb
from django.core.management import call_command
from django.core.management.commands.testserver import Command as TestServerCommand
from django.db import connection

# Adapated from ./manage.py testserver in django/core/management/commands/testserver.py
# Only the line marked "NEW CODE" is edited


class Command(TestServerCommand):
    help = (
        "Runs a test server with data from the given fixture(s) and creates a template."
    )

    def handle(self, *fixture_labels, **options):
        verbosity = options["verbosity"]
        interactive = options["interactive"]

        # Create a test database.
        db_name = connection.creation.create_test_db(
            verbosity=verbosity, autoclobber=not interactive, serialize=False
        )

        # Import the fixture data into the test database.
        call_command("loaddata", *fixture_labels, **{"verbosity": verbosity})

        # NEW CODE: Build a duplicate database as a template
        create_template_from_testdb()

        # Run the development server. Turn off auto-reloading because it causes
        # a strange error -- it causes this handle() method to be called
        # multiple times.
        shutdown_message = (
            "\nServer stopped.\nNote that the test database, %r, has not been "
            "deleted. You can explore it on your own." % db_name
        )
        use_threading = connection.features.test_db_allows_multiple_connections
        call_command(
            "runserver",
            addrport=options["addrport"],
            shutdown_message=shutdown_message,
            use_reloader=False,
            use_ipv6=options["use_ipv6"],
            use_threading=use_threading,
        )
