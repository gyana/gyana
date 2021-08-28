import vcr
from django.core.management.commands import runserver

CYPRESS_CASETTE = None


class Command(runserver.Command):
    def inner_run(self, *args, **options):
        with vcr.use_cassette("cypress/fixtures/vcr/temporary.yaml") as casette:
            global CYPRESS_CASETTE
            CYPRESS_CASETTE = casette
            super().inner_run(self, *args, **options)
