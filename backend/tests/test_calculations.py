import unittest
import datetime
from backend.app.services.calculation_service import CalculationService
from backend.app.models.models import Vehicle, FuelRecord, MaintenanceRecord, ExpenseRecord

class TestCalculationService(unittest.TestCase):

    def test_odometer_validation(self):
        # Odômetro igual ou maior deve ser válido
        valid, msg = CalculationService.validate_odometer(50000, 50100)
        self.assertTrue(valid)
        self.assertIsNone(msg)

        # Odômetro menor deve alertar
        valid, msg = CalculationService.validate_odometer(50000, 49900)
        self.assertFalse(valid)
        self.assertIn("menor que o último registro", msg)

    def test_fuel_consumption_consecutive(self):
        # 1o abastecimento: 10.000 km
        prev = FuelRecord(odometer=10000, liters=40.0)
        # 2o abastecimento: 10.450 km com 45L => 450 km / 45L = 10.0 km/L
        consump = CalculationService.calculate_fuel_consumption(prev, 10450, 45.0)
        self.assertEqual(consump, 10.0)

    def test_fuel_consumption_single_refuel_returns_none(self):
        # Não inventar consumo com apenas 1 registro
        consump = CalculationService.calculate_fuel_consumption(None, 10000, 40.0)
        self.assertIsNone(consump)

    def test_dashboard_calculations(self):
        today = datetime.datetime.now(datetime.timezone.utc).strftime("%Y-%m-%d")
        vehicle = Vehicle(id=1, user_id=1, current_odometer=50500, brand="Toyota", model="Corolla", year=2022)

        fuels = [
            FuelRecord(id=1, vehicle_id=1, date=today, odometer=50000, liters=40.0, price_per_liter=5.0, total_cost=200.0, fuel_type="gasoline"),
            FuelRecord(id=2, vehicle_id=1, date=today, odometer=50450, liters=45.0, price_per_liter=5.0, total_cost=225.0, fuel_type="gasoline")
        ]
        maintenances = [
            MaintenanceRecord(id=1, vehicle_id=1, date=today, odometer=50000, category="oil", description="Troca de óleo", cost=300.0, next_due_odometer=60000)
        ]
        expenses = [
            ExpenseRecord(id=1, vehicle_id=1, date=today, category="washing", description="Ducha", amount=50.0)
        ]

        dash = CalculationService.calculate_dashboard(vehicle, fuels, maintenances, expenses)
        # Total do mês = 200 + 225 + 300 + 50 = 775.0
        self.assertEqual(dash.monthly_total, 775.0)
        self.assertEqual(dash.monthly_fuel, 425.0)
        self.assertEqual(dash.monthly_maintenance, 300.0)
        self.assertEqual(dash.monthly_other, 50.0)
        self.assertEqual(dash.average_consumption, 10.0)
        self.assertEqual(dash.next_maintenance_km_remaining, 9500)
        self.assertGreater(dash.fuel_expense_percentage, 50.0)

if __name__ == '__main__':
    unittest.main()
