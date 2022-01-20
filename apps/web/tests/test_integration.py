import pytest

from apps.base.tests.asserts import assertLink, assertOK
from apps.users.models import CustomUser

pytestmark = pytest.mark.django_db


def test_site_pages(client):
    r = client.get("/")
    assertOK(r)

    r = client.get("/pricing")
    assertOK(r)

    r = client.get("/integrations")
    assertOK(r)

    r = client.get("/about")
    assertOK(r)

    r = client.get("/privacy-policy")
    assertOK(r)

    r = client.get("/terms-of-use")
    assertOK(r)


def test_site_links(client):

    r = client.get("/")

    # header links
    # 3x = header, mobile menu, footer
    assertLink(r, "/agency", "Agency", total=3)
    assertLink(r, "/#integrations", "Integrations", total=3)
    assertLink(r, "/#workflows", "Workflows", total=3)
    assertLink(r, "/#dashboards", "Dashboards", total=3)
    assertLink(r, "/pricing", "Pricing", total=3)
    assertLink(r, "/blog", "Blog", total=3)
    assertLink(r, "https://intercom.help/gyana", "Help Center", total=3)
    assertLink(r, "https://feedback.gyana.com", "Feedback", total=3)

    assertLink(r, "/integrations", "View our integrations.")

    # footer links
    assertLink(r, "/about", "About", total=2)
    assertLink(r, "/about#careers", "Careers")
    assertLink(
        r,
        "https://c6df0725-5be1-435b-a2d7-1a90649a7bc5.site.hbuptime.com/",
        "Status page",
    )
    assertLink(r, "/privacy-policy", "Privacy")
    assertLink(r, "/terms-of-use", "Terms")

    # app links
    assertLink(
        r, "https://gyana-data.typeform.com/to/v2XTy0j3", "Request access", total=4
    )
    assertLink(r, "/login/", "Sign in", total=2)

    user = CustomUser.objects.create_user("test", email="test@gyana.com")
    client.force_login(user)

    r = client.get("/pricing")
    assertLink(r, "/", "Go to app", total=2)
