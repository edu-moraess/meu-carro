import unittest
from backend.app.ai.gemini_service import GeminiService

class TestAiService(unittest.TestCase):

    def test_parse_fuel_text(self):
        text = "Abasteci 40 litros de gasolina a 5.89 no posto Ipiranga com 45000 km e gastei 235.60"
        parsed = GeminiService.parse_natural_text(text)
        self.assertEqual(parsed.type, "fuel")
        self.assertEqual(parsed.odometer, 45000)
        self.assertEqual(parsed.liters, 40.0)
        self.assertEqual(parsed.price_per_liter, 5.89)
        self.assertAlmostEqual(parsed.total_cost, 235.60, places=2)
        self.assertEqual(parsed.fuel_type, "gasoline")
        self.assertGreaterEqual(parsed.confidence, 0.8)

    def test_parse_maintenance_text(self):
        text = "Fiz troca de oleo na oficina do Joao com 52000 km e paguei 280"
        parsed = GeminiService.parse_natural_text(text)
        self.assertEqual(parsed.type, "maintenance")
        self.assertEqual(parsed.odometer, 52000)
        self.assertEqual(parsed.category, "oil")
        self.assertEqual(parsed.total_cost, 280.0)

    def test_parse_expense_text(self):
        text = "Paguei 45 de lavagem do carro ontem"
        parsed = GeminiService.parse_natural_text(text)
        self.assertEqual(parsed.type, "expense")
        self.assertEqual(parsed.category, "washing")
        self.assertEqual(parsed.total_cost, 45.0)

if __name__ == '__main__':
    unittest.main()
