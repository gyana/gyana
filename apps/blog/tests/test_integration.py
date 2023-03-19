import pytest
from pytest_django.asserts import assertContains

from apps.base.tests.asserts import assertLink, assertOK

pytestmark = pytest.mark.django_db


def test_blog(client, post_factory):
    post = post_factory()

    r = client.get("/blog/")
    assertOK(r)

    assertContains(r, "Blog")
    assertContains(r, "Learn about tips, product updates and our journey.")

    assertLink(r, "/blog/gyana-2021-wrapped", "Gyana 2021, Wrapped")

    r = client.get("/blog/gyana-2021-wrapped")
    assertOK(r)

    assertContains(r, "Han Solo")
    assertContains(r, "Gyana 2021, Wrapped")
    assertContains(
        r,
        "We launched Gyana 2.0, built our fantastic community and helped thousands of customers discover new ways to work with data.",
    )
