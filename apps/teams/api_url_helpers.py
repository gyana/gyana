from django.urls import reverse

TEAM_PLACEHOLDER = "__team_slug__"
INVITATION_PLACEHOLDER = "__invite_id__"


def get_team_api_url_templates():
    invite_api_url_names = {"single_team:resend_invitation"}
    return {
        api_url: reverse(api_url, args=[TEAM_PLACEHOLDER, INVITATION_PLACEHOLDER])
        for api_url in invite_api_url_names
    }
