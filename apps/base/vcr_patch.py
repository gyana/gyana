import vcr
from django.core.management.commands import runserver

CYPRESS_CASETTE = None
CASETTE_PATH = "cypress/fixtures/vcr"

inner_run = runserver.Command.inner_run


def new_inner_run(self, *args, **options):
    print("runserver with casette")
    with vcr.use_cassette(f"{CASETTE_PATH}/temporary.yaml") as casette:
        global CYPRESS_CASETTE
        CYPRESS_CASETTE = casette
        inner_run(self, *args, **options)


runserver.Command.inner_run = new_inner_run
