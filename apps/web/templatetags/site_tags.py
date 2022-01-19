from django import template

EXTERNAL_URLS = {
    "waitlist": "https://gyana-data.typeform.com/to/v2XTy0j3",
    "status": "https://c6df0725-5be1-435b-a2d7-1a90649a7bc5.site.hbuptime.com/",
    "feedback": "https://feedback.gyana.com",
    "help": "https://intercom.help/gyana",
    "newsletter": "http://eepurl.com/gAi94b",
    # social
    "facebook": "https://www.facebook.com/GyanaHQ",
    "twitter": "https://twitter.com/GyanaHQ",
    "instagram": "https://www.instagram.com/gyaanaa",
    "linkedin": "https://www.linkedin.com/company/gyana",
    "youtube": "https://www.youtube.com/gyana",
}

register = template.Library()


@register.simple_tag
def external_url(name: str):
    return EXTERNAL_URLS[name]
