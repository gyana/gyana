from apps.utils.test import create_testdb_from_template
from django.core.management import call_command
from django.http.response import HttpResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request


@api_view(["GET"])
@permission_classes([AllowAny])
def resetdb(request: Request):

    # Delete all data from the database.
    call_command("flush", interactive=False)

    # Import the fixture data into the database.
    call_command("loaddata", "cypress/fixtures/fixtures.json")

    return HttpResponse()
