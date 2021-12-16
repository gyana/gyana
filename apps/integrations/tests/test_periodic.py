from datetime import timedelta

import pytest
from django.utils import timezone

from apps.integrations import periodic
from apps.integrations.models import Integration

PENDING_DELETE_AFTER_DAYS = 7

pytestmark = pytest.mark.django_db


def test_delete_outdated_pending_integrations(logged_in_user, integration_factory):

    # test: only deletes pending integrations more than 7 days old
    # this logic is critical as it involves deletion

    integration = integration_factory(project__team=logged_in_user.teams.first())

    integration.created = timezone.now() - timedelta(days=PENDING_DELETE_AFTER_DAYS + 1)
    integration.save()
    assert Integration.objects.count() == 1

    periodic.delete_outdated_pending_integrations.delay()
    assert Integration.objects.count() == 1

    integration.created = timezone.now() - timedelta(days=PENDING_DELETE_AFTER_DAYS - 1)
    integration.ready = False
    integration.save()

    periodic.delete_outdated_pending_integrations.delay()
    assert Integration.objects.count() == 1

    integration.created = timezone.now() - timedelta(days=PENDING_DELETE_AFTER_DAYS + 1)
    integration.save()

    periodic.delete_outdated_pending_integrations.delay()
    assert Integration.objects.count() == 0
