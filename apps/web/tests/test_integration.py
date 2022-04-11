import pytest
import wagtail_factories
from pytest_django.asserts import assertContains, assertNotContains
from wagtail.core.models import Locale, Site

from apps.base.tests.asserts import assertLink, assertOK
from apps.users.models import CustomUser

pytestmark = pytest.mark.django_db


def test_site_pages(client):
    r = client.get("/")
    assertOK(r)

    r = client.get("/pricing")
    assertOK(r)

    r = client.get("/about")
    assertOK(r)

    r = client.get("/privacy-policy")
    assertOK(r)

    r = client.get("/terms-of-use")
    assertOK(r)

    r = client.get("/book-a-demo")
    assertOK(r)

    r = client.get("/use-case/ecommerce")
    assertOK(r)
    r = client.get("/use-case/b2b-saas")
    assertOK(r)
    r = client.get("/use-case/marketing-agency")
    assertOK(r)

    r = client.get("/demo/integrations")
    assertOK(r)
    r = client.get("/demo/workflows")
    assertOK(r)
    r = client.get("/demo/dashboards")
    assertOK(r)
    r = client.get("/demo/support")
    assertOK(r)
    r = client.get("/demo/intercom")
    assertOK(r)


def test_site_links(client):

    r = client.get("/")

    # header links
    # 3x = header, mobile menu, footer
    assertLink(r, "/integrations", "Integrations", total=3)
    assertLink(r, "/pricing", "Pricing", total=3)
    assertLink(r, "/blog", "Blog", total=3)
    assertLink(r, "https://support.gyana.com", "Help Center", total=3)
    assertLink(r, "https://feedback.gyana.com", "Feedback", total=3)

    assertLink(r, "/use-case/ecommerce", "Ecommerce", total=3)
    assertLink(r, "/use-case/b2b-saas", "B2B Saas", total=3)
    assertLink(r, "/use-case/marketing-agency", "Marketing Agency", total=3)

    assertLink(r, "/integrations", "Learn about integrations")

    # footer links
    assertLink(r, "/about", "About", total=3)
    assertLink(r, "/about#careers", "Careers")
    assertLink(
        r,
        "https://c6df0725-5be1-435b-a2d7-1a90649a7bc5.site.hbuptime.com/",
        "Status page",
    )
    assertLink(r, "/privacy-policy", "Privacy")
    assertLink(r, "/terms-of-use", "Terms")

    # app links
    assertLink(r, "/signup/", "Sign up", total=4)
    assertLink(r, "/book-a-demo", "Book a demo", total=4)
    assertLink(r, "/login/", "Sign in", total=2)

    user = CustomUser.objects.create_user("test", email="test@gyana.com")
    client.force_login(user)

    r = client.get("/pricing")
    assertLink(r, "/", "Go to app", total=2)


def test_integrations_page(client):

    r = client.get("/integrations")
    assertOK(r)

    assertLink(r, "/book-a-demo", "Talk to us", total=2)

    # integration search
    r = client.get("/demo/search-integrations")
    assertOK(r)

    r = client.get("/demo/search-integrations?query=google")
    assertOK(r)
    assertContains(r, "Google Ads")
    assertLink(r, "/integrations/adwords", "Google Ads")
    assertNotContains(r, "Facebook Pages")

    r = client.get("/demo/search-integrations?category=Organic")
    assertOK(r)
    assertContains(r, "Facebook Pages")
    assertLink(r, "/integrations/facebook_pages", "Facebook Pages")
    assertNotContains(r, "Google Ads")

    r = client.get("/integrations/adwords")
    assertOK(r)


def test_sitemap(client):
    locale = Locale.objects.create(language_code="en")
    root_page = wagtail_factories.PageFactory(parent=None, title="Root")
    site = Site.objects.create(is_default_site=True, root_page=root_page)

    # sitemap
    r = client.get("/sitemap.xml")
    assertOK(r)
