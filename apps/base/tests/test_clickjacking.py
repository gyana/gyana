import pytest
import wagtail_factories
from wagtail.core.models import Locale, Site

pytestmark = pytest.mark.django_db


def test_xframe_options_sameorigin_allowlist(client, learn_page_factory):

    locale = Locale.objects.create(language_code="en")
    root_page = wagtail_factories.PageFactory(parent=None, title="Root")
    site = Site.objects.create(is_default_site=True, root_page=root_page)
    learn_page = learn_page_factory(parent=root_page)

    # no header
    r = client.get("/learn/")
    assert r["X-FRAME-OPTIONS"] == "DENY"

    # referer URL does not exist
    r = client.get("/learn/", HTTP_REFERER="/does/not/exist")
    assert r["X-FRAME-OPTIONS"] == "DENY"

    # referer URL not on allowlist
    r = client.get("/learn/", HTTP_REFERER="/integrations")
    assert r["X-FRAME-OPTIONS"] == "DENY"

    # requested URL is not exempt
    r = client.get("/integrations/", HTTP_REFERER="/")
    assert r["X-FRAME-OPTIONS"] == "DENY"

    # success
    r = client.get("/learn/", HTTP_REFERER="/")
    assert r["X-FRAME-OPTIONS"] == "SAMEORIGIN"
