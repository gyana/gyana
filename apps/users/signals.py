# avoid multiple email logins
# https://github.com/pennersr/django-allauth/issues/1109

from datetime import datetime

import analytics
from allauth.account.models import EmailAddress
from allauth.account.signals import email_confirmed, user_signed_up
from django.dispatch.dispatcher import receiver

from apps.appsumo.models import AppsumoCode
from apps.base.analytics import SIGNED_UP_EVENT, identify_user
from apps.invites.models import Invite
from apps.users.models import ApprovedWaitlistEmail


@receiver(email_confirmed)
def update_user_email(sender, request, email_address, **kwargs):
    # Once the email address is confirmed, make new email_address primary.
    # This also sets user.email to the new email address.
    # email_address is an instance of allauth.account.models.EmailAddress
    email_address.set_as_primary()
    EmailAddress.objects.filter(user=email_address.user).exclude(primary=True).delete()


@receiver(user_signed_up)
def identify_user_after_signup(request, user, **kwargs):

    signup_source = "website"

    if Invite.check_email_invited(user.email):
        signup_source = "invite"
    elif ApprovedWaitlistEmail.check_approved(user.email):
        signup_source = "waitlist"
    elif (
        user.date_joined < datetime(2022, 2, 10)
        or AppsumoCode.filter(redeemed_by=user).exists
    ):
        signup_source = "appsumo"

    identify_user(user, signup_source)
    analytics.track(user.id, SIGNED_UP_EVENT)
