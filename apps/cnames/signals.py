from django.db.models.signals import post_delete
from django.dispatch.dispatcher import receiver

from .heroku import delete_heroku_domain
from .models import CName


@receiver(post_delete, sender=CName)
def delete_heroku_domain_signal(sender, instance, *args, **kwargs):
    delete_heroku_domain(instance)
