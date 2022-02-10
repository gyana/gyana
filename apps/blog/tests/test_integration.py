import pytest
import wagtail_factories
from pytest_django.asserts import assertContains
from wagtail.core.models import Locale, Site

from apps.base.tests.asserts import assertLink, assertOK

pytestmark = pytest.mark.django_db


def test_blog(client, blog_index_page_factory, blog_page_factory):
    locale = Locale.objects.create(language_code="en")
    root_page = wagtail_factories.PageFactory(parent=None, title="Root")
    site = Site.objects.create(is_default_site=True, root_page=root_page)
    blog_index_page = blog_index_page_factory(parent=root_page)
    blog_page = blog_page_factory(parent=blog_index_page)

    r = client.get("/blog/")
    assertOK(r)

    assertContains(r, "Blog")
    assertContains(r, "Learn about tips, product updates and company culture.")
    assertContains(r, "News")  # category

    assertLink(r, "/blog/gyana-2021-wrapped/", "Gyana 2021, Wrapped")

    r = client.get("/blog/gyana-2021-wrapped/")
    assertOK(r)

    assertContains(r, "Han Solo")
    assertContains(r, "Gyana 2021, Wrapped")
    assertContains(
        r,
        "We launched Gyana 2.0, built our fantastic community and helped thousands of customers discover new ways to work with data.",
    )
