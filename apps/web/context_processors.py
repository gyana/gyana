from copy import copy

from django.conf import settings

from .meta import absolute_url


def user_meta(request):
    return {"sidebar_collapsed": request.session.get("sidebar_collapsed", False)}


def project_meta(request):
    # modify these values as needed and add whatever else you want globally available here
    project_data = copy(settings.PROJECT_METADATA)
    project_data["TITLE"] = "{} | {}".format(
        project_data["NAME"], project_data["DESCRIPTION"]
    )

    return {
        "project_meta": project_data,
        "page_url": absolute_url(request.path),
        "page_title": "",
        "page_description": "",
        "page_image": "",
    }


def google_analytics_id(request):
    """
    Adds google analytics id to all requests
    """
    return {
        "GOOGLE_ANALYTICS_ID": settings.GOOGLE_ANALYTICS_ID,
        "WEBSITE_GTM_ID": settings.WEBSITE_GTM_ID,
    }
