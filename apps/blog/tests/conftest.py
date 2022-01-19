from datetime import date

import factory
import pytest
import wagtail_factories
from pytest_factoryboy import register

from apps.blog.models import BlogAuthor, BlogCategory, BlogIndexPage, BlogPage

pytestmark = pytest.mark.django_db


@register
class BlogAuthorFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BlogAuthor

    name = "Han Solo"


@register
class BlogCategoryFactory(factory.django.DjangoModelFactory):
    class Meta:
        model = BlogCategory

    name = "News"


@register
class BlogIndexPageFactory(wagtail_factories.PageFactory):
    title = "Blog"
    intro = "Learn about tips, product updates and company culture."

    class Meta:
        model = BlogIndexPage


@register
class BlogPageFactory(wagtail_factories.PageFactory):
    title = "Gyana 2021, Wrapped"
    slug = "gyana-2021-wrapped"
    date = date(2022, 1, 1)
    intro = "2021 was a good year for Gyana."
    body = "We launched Gyana 2.0, built our fantastic community and helped thousands of customers discover new ways to work with data."
    category = factory.SubFactory(BlogCategoryFactory)
    author = factory.SubFactory(BlogAuthorFactory)

    class Meta:
        model = BlogPage
