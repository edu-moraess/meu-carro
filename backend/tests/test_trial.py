import unittest
import datetime
from backend.app.models.models import User
from backend.app.services.subscription_service import SubscriptionService

class TestTrialSubscription(unittest.TestCase):

    def test_trial_active_30_days(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        user = User(
            id=1,
            email="novo@meucarro.app",
            plan="trial",
            trial_started_at=now,
            trial_ends_at=now + datetime.timedelta(days=30),
            is_active=True
        )
        status = SubscriptionService.get_subscription_status(user)
        self.assertTrue(status.trial_active)
        self.assertGreaterEqual(status.trial_days_remaining, 29)
        self.assertIsNone(status.warning_message)

    def test_trial_warning_3_days(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        user = User(
            id=2,
            email="aviso@meucarro.app",
            plan="trial",
            trial_started_at=now - datetime.timedelta(days=27),
            trial_ends_at=now + datetime.timedelta(days=3),
            is_active=True
        )
        status = SubscriptionService.get_subscription_status(user)
        self.assertTrue(status.trial_active)
        self.assertEqual(status.trial_days_remaining, 3)
        self.assertIsNotNone(status.warning_message)
        self.assertIn("termina em 3 dias", status.warning_message)

    def test_trial_expired(self):
        now = datetime.datetime.now(datetime.timezone.utc)
        user = User(
            id=3,
            email="expirado@meucarro.app",
            plan="trial",
            trial_started_at=now - datetime.timedelta(days=35),
            trial_ends_at=now - datetime.timedelta(days=5),
            is_active=True
        )
        status = SubscriptionService.get_subscription_status(user)
        self.assertFalse(status.trial_active)
        self.assertEqual(status.trial_days_remaining, 0)

if __name__ == '__main__':
    unittest.main()
