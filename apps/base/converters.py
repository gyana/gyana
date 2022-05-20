# https://spapas.github.io/2021/01/07/django-hashids/

from django.conf import settings
from django.core.exceptions import ValidationError
from hashids import Hashids

hashids = Hashids(settings.HASHIDS_SALT, min_length=8)


def h_encode(id):
    return hashids.encode(id)


def h_decode(h):
    z = hashids.decode(h)

    if z:
        return z[0]
    else:
        # Will return a 404 page in production
        raise ValueError("Provided hashid is invalid")


class HashIdConverter:
    regex = "[a-zA-Z0-9]{8,}"

    def to_python(self, value):
        return h_decode(value)

    def to_url(self, value):
        return h_encode(value)
