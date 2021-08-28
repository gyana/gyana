from apps.base.clients import fivetran_client
from apps.base.cypress_mail import Outbox
from apps.base.management.commands.cypress_server import CASETTE_PATH, CYPRESS_CASETTE
from apps.integrations.tasks import delete_outdated_pending_integrations
from apps.teams.tasks import update_team_row_limits
from django.core import mail
from django.core.management import call_command
from django.http.response import JsonResponse
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

    mail.outbox = Outbox()
    mail.outbox.clear()

    fivetran_client()._schema_cache.clear()
    fivetran_client()._started = {}

    return JsonResponse({})


@api_view(["GET"])
@permission_classes([AllowAny])
def outbox(request: Request):

    messages = mail.outbox.messages if hasattr(mail, "outbox") else []

    return JsonResponse({"messages": messages, "count": len(messages)})


@api_view(["GET"])
@permission_classes([AllowAny])
def periodic(request: Request):

    # force all periodic tasks to run synchronously

    delete_outdated_pending_integrations()
    update_team_row_limits()

    return JsonResponse({"message": "ok"})


@api_view(["GET"])
@permission_classes([AllowAny])
def start_vcr(request: Request, name: str):

    # load a new casette into the existing stubbed context
    # See kevin1024/vcrpy/vcr/cassette.py
    CYPRESS_CASETTE._path = f"{CASETTE_PATH}/{name}.yaml"
    CYPRESS_CASETTE.data = []
    CYPRESS_CASETTE.rewind()
    CYPRESS_CASETTE._load()

    return JsonResponse({"message": "ok"})


@api_view(["GET"])
@permission_classes([AllowAny])
def stop_vcr(request: Request):
    from apps.base.management.commands.cypress_server import CYPRESS_CASETTE

    CYPRESS_CASETTE._save()

    return JsonResponse({"message": "ok"})
