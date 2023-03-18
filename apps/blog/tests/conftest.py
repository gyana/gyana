from datetime import date

import factory
import pytest
from pytest_factoryboy import register

from apps.blog.models import Author, Post

pytestmark = pytest.mark.django_db


@register
class AuthorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = Author

    name = "Han Solo"


@register
class PostFactory(factory.django.DjangoModelFactory):
    title = "Gyana 2021, Wrapped"
    slug = "gyana-2021-wrapped"
    date = date(2022, 1, 1)
    intro = "2021 was a good year for Gyana."
    body = "We launched Gyana 2.0, built our fantastic community and helped thousands of customers discover new ways to work with data."
    author = factory.SubFactory(AuthorFactory)

    class Meta:
        model = Post
