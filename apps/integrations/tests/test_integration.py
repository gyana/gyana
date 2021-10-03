import pytest
from apps.base.tests.asserts import assertFormRenders, assertLink, assertOK
from apps.users.models import CustomUser
from django.core import mail
from pytest_django.asserts import assertContains, assertRedirects

pytestmark = pytest.mark.django_db


def test_structure_and_preview(client, logged_in_user):
    pass


def test_update_and_delete(client, logged_in_user):
    pass


def test_create_retry_edit_and_approve(client):
    pass


def test_row_limits(client, logged_in_user):
    pass


def test_pending_cleanup(client, logged_in_user):
    pass
