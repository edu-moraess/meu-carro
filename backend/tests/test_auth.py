import unittest
import time
from backend.app.security.passwords import hash_password, verify_password
from backend.app.security.tokens import create_access_token, decode_access_token

class TestAuthSecurity(unittest.TestCase):

    def test_password_hash_and_verify(self):
        pw = "MinhaSenhaForte2026@"
        hashed = hash_password(pw)
        self.assertTrue(hashed.startswith("pbkdf2_sha256$"))
        self.assertTrue(verify_password(pw, hashed))
        self.assertFalse(verify_password("SenhaIncorreta", hashed))

    def test_jwt_token_flow(self):
        payload = {"sub": "42", "email": "test@meucarro.app"}
        token = create_access_token(payload, expires_delta_seconds=3600)
        self.assertIsInstance(token, str)
        self.assertEqual(len(token.split('.')), 3)

        decoded = decode_access_token(token)
        self.assertIsNotNone(decoded)
        self.assertEqual(decoded["sub"], "42")
        self.assertEqual(decoded["email"], "test@meucarro.app")

    def test_jwt_token_tampered(self):
        payload = {"sub": "42"}
        token = create_access_token(payload, expires_delta_seconds=3600)
        parts = token.split('.')
        tampered = parts[0] + '.' + parts[1] + '.invalid_signature'
        self.assertIsNone(decode_access_token(tampered))

    def test_jwt_token_expired(self):
        payload = {"sub": "42"}
        token = create_access_token(payload, expires_delta_seconds=-10)
        self.assertIsNone(decode_access_token(token))

if __name__ == '__main__':
    unittest.main()
