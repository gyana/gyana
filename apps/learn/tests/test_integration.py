import json
from uuid import uuid4

import pytest
import wagtail_factories
from pytest_django.asserts import assertContains, assertNotContains
from wagtail.core.models import Locale, Site

from apps.base.tests.asserts import (
    assertFormRenders,
    assertLink,
    assertOK,
    assertSelectorLength,
)

pytestmark = pytest.mark.django_db

RICH_TEXT_BLOCK = {
    "type": "text",
    "value": "Gyana has many integrations <h2>Connectors</h2>",
    "id": str(uuid4()),
}


def test_learn(client, user, learn_page_factory):
    locale = Locale.objects.create(language_code="en")
    root_page = wagtail_factories.PageFactory(parent=None, title="Root")
    site = Site.objects.create(is_default_site=True, root_page=root_page)
    learn_page = learn_page_factory(parent=root_page)
    getting_started_page = learn_page_factory(
        parent=learn_page, slug="getting-started", title="Getting started"
    )
    guide_page = learn_page_factory(parent=learn_page, slug="guides", title="Guides")
    integrations_page = learn_page_factory(
        parent=guide_page,
        slug="integrations",
        title="Integrations",
        body=json.dumps([RICH_TEXT_BLOCK]),
    )
    workflows_page = learn_page_factory(
        parent=guide_page, slug="workflows", title="Workflows"
    )

    r = client.get("/learn/")
    assertOK(r)

    assertLink(r, "/learn", "University")
    assertLink(r, "/learn", "Home")
    assertLink(r, "/", "Website")
    assertContains(r, "Welcome to Gyana University")

    # sidebar navigation
    assertLink(r, "/learn/getting-started/", "Getting started")
    assertLink(r, "/learn/guides/", "Guides")
    assertNotContains(r, "Integrations")

    # check for child rendering behaviour
    r = client.get("/learn/guides/")
    assertLink(r, "/learn/guides/integrations/", "Integrations")

    r = client.get("/learn/guides/integrations/")

    # parent is rendered in sidebar
    # todo: breadcrumbs
    assertLink(r, "/learn/guides/", "Guides")
    # content
    assertContains(r, "Integrations")
    assertContains(r, "Gyana has many integrations")
    # previous/next links
    assertLink(r, "/learn/guides/workflows/", "Next")
    # sub-headings in content and right sidebar
    assertLink(r, "#connectors", "Connectors", total=2)

    #  logged in user sees "go to app"
    client.force_login(user)
    r = client.get("/learn/")
    assertOK(r)

    assertLink(r, "/", "Go to app")


def test_learn_search(client, user, learn_page_factory):
    locale = Locale.objects.create(language_code="en")
    root_page = wagtail_factories.PageFactory(parent=None, title="Root")
    site = Site.objects.create(is_default_site=True, root_page=root_page)
    learn_page = learn_page_factory(parent=root_page)
    getting_started_page = learn_page_factory(
        parent=learn_page, slug="getting-started", title="Getting started"
    )
    guide_page = learn_page_factory(parent=learn_page, slug="guides", title="Guides")
    integrations_page = learn_page_factory(
        parent=guide_page,
        slug="integrations",
        title="Integrations",
        body=json.dumps([RICH_TEXT_BLOCK]),
    )

    r = client.get("/learn/search?query=integrations")
    assertOK(r)

    assertSelectorLength(r, "dt", 1)
    assertLink(r, "/learn/guides/integrations/", "Gyana has many integrations")

    r = client.get("/learn/search?query=does-not-exist")
    assertOK(r)
    assertSelectorLength(r, "dt", 0)
    assertContains(r, "No results found")
