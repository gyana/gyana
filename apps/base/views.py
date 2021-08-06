from django.core import mail
from django.core.management import call_command
from django.http.response import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.request import Request


def _msg_to_dict(msg):
    return {
        "payload": msg.message().get_payload(),
        **{k: v for k, v in msg.message().items()},
    }


@api_view(["GET"])
@permission_classes([AllowAny])
def resetdb(request: Request):

    # Delete all data from the database.
    call_command("flush", interactive=False)

    # Import the fixture data into the database.
    call_command("loaddata", "cypress/fixtures/fixtures.json")

    mail.outbox = []

    return JsonResponse({})


@api_view(["GET"])
@permission_classes([AllowAny])
def outbox(request: Request):

    outbox = getattr(mail, "outbox", [])

    messages = [_msg_to_dict(msg) for msg in outbox]

    return JsonResponse({"messages": messages, "count": len(messages)})
