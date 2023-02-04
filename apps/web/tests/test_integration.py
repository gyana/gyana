import pytest
import wagtail_factories
from djpaddle.models import Plan
from wagtail.core.models import Locale, Site

from apps.base.tests.asserts import assertLink, assertOK
from apps.users.models import CustomUser

pytestmark = pytest.mark.django_db


def test_site_pages(client, settings):

    pro_plan = Plan.objects.create(name="Pro", billing_type="month", billing_period=1)
    settings.DJPADDLE_PRO_PLAN_ID = pro_plan.id

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

    r = client.get("/demo/integrations")
    assertOK(r)
    r = client.get("/demo/workflows")
    assertOK(r)
    r = client.get("/demo/dashboards")
    assertOK(r)
    r = client.get("/demo/support")
    assertOK(r)


def test_site_links(client, settings):

    pro_plan = Plan.objects.create(name="Pro", billing_type="month", billing_period=1)
    settings.DJPADDLE_PRO_PLAN_ID = pro_plan.id

    r = client.get("/")

    # header links
    # 3x = header, mobile menu, footer
    assertLink(r, "/pricing", "Pricing", total=3)
    assertLink(r, "/blog", "Blog", total=3)
    assertLink(r, "https://support.gyana.com", "Documentation", total=3)
    assertLink(r, "https://feedback.gyana.com", "Feedback", total=3)

    # footer links
    assertLink(r, "/about", "About", total=3)
    assertLink(
        r,
        "https://c6df0725-5be1-435b-a2d7-1a90649a7bc5.site.hbuptime.com/",
        "Status page",
    )
    assertLink(r, "/privacy-policy", "Privacy")
    assertLink(r, "/terms-of-use", "Terms")

    # app links
    assertLink(r, "/signup/", "Sign up", total=3)
    assertLink(r, "/login/", "Sign in", total=2)

    user = CustomUser.objects.create_user("test", email="test@gyana.com")
    client.force_login(user)

    r = client.get("/pricing")
    assertLink(r, "/", "Go to app", total=2)


def test_sitemap(client):
    locale = Locale.objects.create(language_code="en")
    root_page = wagtail_factories.PageFactory(parent=None, title="Root")
    site = Site.objects.create(is_default_site=True, root_page=root_page)

    # sitemap
    r = client.get("/sitemap.xml")
    assertOK(r)
