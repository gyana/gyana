# avoid multiple email logins
# https://github.com/pennersr/django-allauth/issues/1109

from allauth.account.models import EmailAddress
from allauth.account.signals import email_confirmed
from django.dispatch.dispatcher import receiver


@receiver(email_confirmed)
def update_user_email(sender, request, email_address, **kwargs):
    # Once the email address is confirmed, make new email_address primary.
    # This also sets user.email to the new email address.
    # email_address is an instance of allauth.account.models.EmailAddress
    email_address.set_as_primary()
    EmailAddress.objects.filter(user=email_address.user).exclude(primary=True).delete()
