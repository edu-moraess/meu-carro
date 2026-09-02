import hashlib
import os
import secrets
import hmac

def hash_password(password: str) -> str:
    """Gera hash seguro com PBKDF2-HMAC-SHA256 e salt de 16 bytes."""
    salt = os.urandom(16)
    pw_hash = hashlib.pbkdf2_hmac('sha256', password.encode('utf-8'), salt, 100000)
    return f"pbkdf2_sha256$100000${salt.hex()}${pw_hash.hex()}"

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifica senha contra o hash armazenado de forma constante contra timing attacks."""
    try:
        parts = hashed_password.split('$')
        if len(parts) != 4 or parts[0] != "pbkdf2_sha256":
            return False
        iterations = int(parts[1])
        salt = bytes.fromhex(parts[2])
        expected_hash = bytes.fromhex(parts[3])
        computed_hash = hashlib.pbkdf2_hmac('sha256', plain_password.encode('utf-8'), salt, iterations)
        return hmac.compare_digest(expected_hash, computed_hash)
    except Exception:
        return False
