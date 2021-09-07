from django.conf import settings


def django_settings(request):
    return {
        "FF_ALPHA": settings.FF_ALPHA,
        "DEBUG": settings.DEBUG,
        "SEGMENT_ANALYTICS_JS_WRITE_KEY": settings.SEGMENT_ANALYTICS_JS_WRITE_KEY,
        "HONEYBADGER_API_KEY": settings.HONEYBADGER_API_KEY,
        "HONEYBADGER_ENVIRONMENT": settings.HONEYBADGER_ENVIRONMENT
        # Extend this by either separate env var names or unpack all settings
    }
