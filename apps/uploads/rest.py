import datetime
import os
import time

import coreapi
from apps.base.clients import get_bucket
from django.conf import settings
from django.utils.text import slugify
from rest_framework.decorators import api_view, schema
from rest_framework.request import Request
from rest_framework.response import Response
from rest_framework.schemas import AutoSchema


@api_view(["POST"])
@schema(
    AutoSchema(
        manual_fields=[
            coreapi.Field(
                name="filename",
                required=True,
                location="form",
            ),
        ]
    )
)
def generate_signed_url(request: Request):
    filename = request.data["filename"]
    filename, file_extension = os.path.splitext(filename)
    path = f"{settings.CLOUD_NAMESPACE}/integrations/{filename}-{slugify(time.time())}{file_extension}"

    blob = get_bucket().blob(path)
    # This signed URL allows the client to create a Session URI to use as upload pointer.
    # Delegating this to the client, because geographic location matters when starting a session
    # https://cloud.google.com/storage/docs/access-control/signed-urls#signing-resumable
    url = blob.generate_signed_url(
        version="v4",
        expiration=datetime.timedelta(minutes=15),
        method="RESUMABLE",
    )

    return Response({"url": url, "path": path})
