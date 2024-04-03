from django.conf import settings
from django.core.files.storage import FileSystemStorage
from storages.backends.gcloud import GoogleCloudStorage


class PrivateFileSystemStorage(FileSystemStorage):
    location = "storage"


def get_public_storage():
    if settings.ENGINE_URL.startswith("bigquery://"):
        return GoogleCloudStorage(
            bucket_name=settings.GS_PUBLIC_BUCKET_NAME,
            cache_control=settings.GS_PUBLIC_CACHE_CONTROL,
            querystring_auth=False,
        )

    elif settings.ENGINE_URL.startswith("postgresql://"):
        return FileSystemStorage()  # defaults to MEDIA_ROOT

    raise ValueError(f"Gyana doesnt not support this engine URL {settings.ENGINE_URL}")
