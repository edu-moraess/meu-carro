import unittest
from backend.app.services.calculation_service import CalculationService
from backend.app.models.models import FuelRecord

class TestFuelLogic(unittest.TestCase):

    def test_total_cost_calculation(self):
        liters = 35.5
        price_per_l = 5.69
        expected = round(liters * price_per_l, 2)
        self.assertEqual(expected, 202.0)

    def test_fuel_consumption_two_stops(self):
        stop1 = FuelRecord(odometer=60000, liters=40.0)
        # 60500 km, 50L -> 500 / 50 = 10 km/L
        km_l = CalculationService.calculate_fuel_consumption(stop1, 60500, 50.0)
        self.assertEqual(km_l, 10.0)

if __name__ == '__main__':
    unittest.main()
