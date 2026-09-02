import unittest
from backend.app.models.models import User, Vehicle, FuelRecord
from backend.app.security.deps import get_user_vehicle_or_404, HTTPException

class DummyQuery:
    def __init__(self, data):
        self.data = data
    def filter(self, *args, **kwargs):
        return self
    def first(self):
        return self.data

class DummySession:
    def __init__(self, vehicle_to_return):
        self.vehicle_to_return = vehicle_to_return
    def query(self, model):
        return DummyQuery(self.vehicle_to_return)

class TestAuthorizationIsolation(unittest.TestCase):

    def test_user_can_access_own_vehicle(self):
        user1 = User(id=10, email="user1@meucarro.app")
        vehicle1 = Vehicle(id=101, user_id=10, brand="Honda", model="Civic", year=2021)
        db = DummySession(vehicle1)

        result = get_user_vehicle_or_404(vehicle_id=101, current_user=user1, db=db)
        self.assertEqual(result.id, 101)
        self.assertEqual(result.user_id, 10)

    def test_user_cannot_access_other_user_vehicle(self):
        user2 = User(id=20, email="user2@meucarro.app")
        db = DummySession(None)

        with self.assertRaises(HTTPException) as ctx:
            get_user_vehicle_or_404(vehicle_id=101, current_user=user2, db=db)
        self.assertEqual(ctx.exception.status_code, 404)
        self.assertIn("não pertence ao usuário", ctx.exception.detail)

if __name__ == '__main__':
    unittest.main()
