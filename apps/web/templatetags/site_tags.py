from django import template

EXTERNAL_URLS = {
    "status": "https://c6df0725-5be1-435b-a2d7-1a90649a7bc5.site.hbuptime.com/",
    "feedback": "https://feedback.gyana.com",
    "help": "https://intercom.help/gyana",
    "newsletter": "http://eepurl.com/gAi94b",
    "onboarding": "https://calendly.com/lorraine-chabeda/30min",
    "sales": "mailto:joyeeta.das@gyana.com",
    "talk_to_us": "https://gyana-data.typeform.com/to/pgpMNnAq",
    "facebook_group": "https://www.facebook.com/groups/891928461364849/",
    "slack_community": "https://join.slack.com/t/gyanacommunity/shared_invite/zt-vly76dna-dxv12CkXdanlwqMam5zDPQ",
    "university": "/learn",
    "careers": "https://gyanalimited.recruitee.com/",
    # social
    "facebook": "https://www.facebook.com/GyanaHQ",
    "twitter": "https://twitter.com/GyanaHQ",
    "instagram": "https://www.instagram.com/gyaanaa",
    "linkedin": "https://www.linkedin.com/company/gyana",
    "youtube": "https://www.youtube.com/gyana",
    # founders
    "david_linkedin": "https://www.linkedin.com/in/davidkll/",
    "david_twitter": "https://twitter.com/davidkell_",
    "joyeeta_linkedin": "https://www.linkedin.com/in/joyeeta-das-9124471a/",
    "joyeeta_twitter": "https://twitter.com/thisisjoyeeta",
}

register = template.Library()


@register.simple_tag
def external_url(name: str):
    return EXTERNAL_URLS[name]
