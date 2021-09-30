from django.db.models.signals import post_delete
from django.dispatch.dispatcher import receiver
from honeybadger import honeybadger
from requests.models import HTTPError

from apps.base.clients import heroku_client

from .models import CName


@receiver(post_delete, sender=CName)
def delete_heroku_domain(sender, instance, *args, **kwargs):
    try:
        heroku_client().get_domain(instance.domain).remove()
    except HTTPError as e:
        honeybadger.notify(e)
        pass
