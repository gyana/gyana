from django.conf import settings


def django_settings(request):
    return {
        "FF_ALPHA": settings.FF_ALPHA,
        # Extend this by either separate env var names or unpack all settings
    }
