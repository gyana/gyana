import pytest
from pytest_django.asserts import assertContains, assertRedirects

from apps.base.tests.asserts import assertFormRenders, assertLink, assertOK

pytestmark = pytest.mark.django_db


def test_dashboard_crudl(client, project, dashboard_factory):

    LIST = f"/projects/{project.id}/dashboards"

    # zero state
    r = client.get(f"{LIST}/")
    assertOK(r)
    assertFormRenders(r, ["project"])
    assertContains(r, "Create a new dashboard")

    # create
    r = client.post(f"{LIST}/new", data={"project": project.id})
    dashboard = project.dashboard_set.first()
    assert dashboard is not None
    DETAIL = f"{LIST}/{dashboard.id}"
    assertRedirects(r, DETAIL, status_code=303)

    # read
    r = client.get(DETAIL)
    assertOK(r)
    # TODO: Fix this
    assertFormRenders(r, ["name", "kind"])
    # TODO: Fix inner text
    assertLink(r, f"{DETAIL}/delete", "Delete")

    # update/rename
    new_name = "Superduper dashboard"
    r = client.post(DETAIL, data={"name": new_name})
    assertRedirects(r, DETAIL, status_code=303)
    dashboard.refresh_from_db()
    assert dashboard.name == new_name

    # delete
    r = client.get(f"{DETAIL}/delete")
    assertOK(r)
    assertFormRenders(r)
    r = client.delete(f"{DETAIL}/delete")
    assertRedirects(r, f"{LIST}/")
    assert project.dashboard_set.first() is None

    # list with pagination
    dashboard_factory.create_batch(30, project=project)
    r = client.get(f"{LIST}/")
    assertOK(r)
    assertLink(r, f"{LIST}/?page=2", "2")
    r = client.get(f"{LIST}/?page=2")
    assertOK(r)
