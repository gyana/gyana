import pytest

from apps.base.tests.asserts import assertLoginRedirect, assertOK

pytestmark = pytest.mark.django_db


@pytest.mark.parametrize(
    "url",
    [
        pytest.param("/nodes/{}", id="update"),
        pytest.param("/nodes/{}/grid", id="grid"),
        pytest.param("/nodes/{}/name", id="name"),
        pytest.param("/nodes/{}/credit_confirmation", id="credit_confirmation"),
        pytest.param("/nodes/{}/formula", id="formula"),
        pytest.param("/nodes/{}/function_info?function=abs", id="function_info"),
        pytest.param("/nodes/{}/duplicate", id="duplicate"),
    ],
)
def test_node_required(client, url, node_factory, user):
    node = node_factory()
    first_url = url.format(node.id)
    assertLoginRedirect(client, first_url)

    client.force_login(user)
    r = client.get(first_url)
    assert r.status_code == 404

    user_node = node_factory(workflow__project__team=user.teams.first())
    r = client.get(url.format(user_node.id))
    assertOK(r)
