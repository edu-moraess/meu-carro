import unittest
from backend.app.models.models import MaintenanceRecord

class TestMaintenanceLogic(unittest.TestCase):

    def test_maintenance_record_alert_threshold(self):
        current_odometer = 59200
        rec = MaintenanceRecord(
            odometer=50000,
            category="oil",
            description="Troca de óleo",
            cost=250.0,
            next_due_odometer=60000
        )
        remaining = rec.next_due_odometer - current_odometer
        self.assertEqual(remaining, 800)
        # 800 km <= 1000 km -> deve alertar preventivamente
        self.assertLessEqual(remaining, 1000)

if __name__ == '__main__':
    unittest.main()
