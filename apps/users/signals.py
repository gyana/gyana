# avoid multiple email logins
# https://github.com/pennersr/django-allauth/issues/1109

from datetime import datetime

import analytics
import pytz
from allauth.account.models import EmailAddress
from allauth.account.signals import email_confirmed, user_signed_up
from django.dispatch.dispatcher import receiver
from django.utils import timezone

from apps.base.analytics import SIGNED_UP_EVENT, identify_user
from apps.invites.models import Invite
from apps.users.models import ApprovedWaitlistEmail

WEBSITE_SIGNUP_ENABLED_DATE = timezone.make_aware(
    datetime(2022, 2, 10), timezone=pytz.timezone("UTC")
)


def _get_signup_source_from_user(user):

    if Invite.check_email_invited(user.email):
        return "invite"

    if ApprovedWaitlistEmail.check_approved(user.email):
        return "waitlist"

    return "website"


@receiver(email_confirmed)
def update_user_email(sender, request, email_address, **kwargs):
    # Once the email address is confirmed, make new email_address primary.
    # This also sets user.email to the new email address.
    # email_address is an instance of allauth.account.models.EmailAddress
    email_address.set_as_primary()
    EmailAddress.objects.filter(user=email_address.user).exclude(primary=True).delete()


@receiver(user_signed_up)
def identify_user_after_signup(request, user, **kwargs):

    identify_user(user, signup_source=_get_signup_source_from_user(user))
    analytics.track(user.id, SIGNED_UP_EVENT)
