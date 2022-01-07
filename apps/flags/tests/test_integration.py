import pytest
from pytest_django.asserts import assertRedirects

from apps.base.tests.asserts import assertFormRenders, assertOK

pytestmark = pytest.mark.django_db


def test_team_flags(client, logged_in_user, flag_factory):
    team = logged_in_user.teams.first()

    flags = [
        flag_factory(name=f"feature_{idx}", is_public_beta=True) for idx in range(3)
    ]
    hidden_flags = [
        flag_factory(name=f"feature_private"),
        flag_factory(name=f"feature_released", is_public_beta=True, everyone=True),
    ]

    r = client.get(f"/teams/{team.id}/beta")
    assertOK(r)

    assertFormRenders(r, ["flags"])

    r = client.post(f"/teams/{team.id}/beta", data={"flags": [flags[0].id]})
    assertRedirects(r, f"/teams/{team.id}/beta", status_code=303)

    assert team.flags.count() == 1
    assert team.flags.first() == flags[0]
