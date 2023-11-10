from django import template

EXTERNAL_URLS = {
    "status": "https://c6df0725-5be1-435b-a2d7-1a90649a7bc5.site.hbuptime.com/",
    "feedback": "https://feedback.gyana.com",
    "help": "https://support.gyana.com",
    "newsletter": "http://eepurl.com/gAi94b",
    "onboarding": "https://calendly.com/lorraine-chabeda/30min",
    "talk_to_us": "mailto:support@gyana.com",
    "hubspot_meeting": "https://meetings-eu1.hubspot.com/david-kell",
    "facebook_group": "https://www.facebook.com/groups/891928461364849/",
    "slack_community": "https://join.slack.com/t/gyanacommunity/shared_invite/zt-vly76dna-dxv12CkXdanlwqMam5zDPQ",
    "careers": "https://gyanalimited.recruitee.com/",
    "appsumo": "https://appsumo.com/products/gyana/",
    "demo_dashboard": "https://www.gyana.com/dashboards/a7b7458f-8162-4ec9-b92b-5b6911e02d49?embed=true",
    "github": "https://www.github.com/gyana/gyana",
    "hire_an_expert": "",
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
    # blog posts
    "goodbye_gyana": "https://gyana.com/blog/goodbye-gyana",
}

register = template.Library()


@register.simple_tag
def external_url(name: str):
    return EXTERNAL_URLS[name]
