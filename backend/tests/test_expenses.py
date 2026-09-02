import unittest
from backend.app.models.models import ExpenseRecord

class TestExpenseLogic(unittest.TestCase):

    def test_expense_record_creation(self):
        rec = ExpenseRecord(
            vehicle_id=1,
            date="2026-09-02",
            category="toll",
            description="Pedágio Rodovia",
            amount=18.50
        )
        self.assertEqual(rec.category, "toll")
        self.assertEqual(rec.amount, 18.50)

if __name__ == '__main__':
    unittest.main()
