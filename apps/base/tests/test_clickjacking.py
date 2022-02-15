import pytest

pytestmark = pytest.mark.django_db


def test_xframe_options_sameorigin_allowlist(client):

    # no header
    r = client.get("/signup/")
    assert r["X-FRAME-OPTIONS"] == "DENY"

    # referer URL does not exist
    r = client.get("/signup/", HTTP_REFERER="/does/not/exist")
    assert r["X-FRAME-OPTIONS"] == "DENY"

    # referer URL not on allowlist
    r = client.get("/signup/", HTTP_REFERER="/integrations")
    assert r["X-FRAME-OPTIONS"] == "DENY"

    # requested URL is no exempt
    r = client.get("/integrations/", HTTP_REFERER="/")
    assert r["X-FRAME-OPTIONS"] == "DENY"

    # success
    r = client.get("/signup/", HTTP_REFERER="/")
    assert r["X-FRAME-OPTIONS"] == "SAMEORIGIN"
