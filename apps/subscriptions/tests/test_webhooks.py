import json
import os
from django.test import SimpleTestCase

from apps.subscriptions.webhooks import get_plan_data, get_previous_plan_data, get_subscription_id, \
    get_cancel_at_period_end


class WebHookHelperTest(SimpleTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        sample_event_filename = os.path.join(os.path.dirname(__file__), 'data', 'subscription-change-event.json')
        with open(sample_event_filename) as f:
            cls.subscription_change_event = json.loads(f.read())

    def test_get_plan_data(self):
        self.assertEqual('plan_GqvTUw8QwIbChu', get_plan_data(self.subscription_change_event)['id'])

    def test_get_previous_plan_data(self):
        self.assertEqual('plan_GqvV4aKw0sh0Za', get_previous_plan_data(self.subscription_change_event)['id'])

    def test_get_subscription_id(self):
        self.assertEqual('sub_HYmtU2lb7NXDFZ', get_subscription_id(self.subscription_change_event))

    def test_get_cancel_at_period_end(self):
        self.assertEqual(False, get_cancel_at_period_end(self.subscription_change_event))
