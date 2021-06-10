from random import randint

from django import template

register = template.Library()


@register.simple_tag
def random_number(length=5):
    """
    Create a random integer with given length.
    For a length of 3 it will be between 100 and 999.
    For a length of 4 it will be between 1000 and 9999.
    """
    return randint(10 ** (length - 1), (10 ** (length) - 1))
