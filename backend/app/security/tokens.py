import json
import base64
import hmac
import hashlib
import time
from typing import Optional, Dict, Any
from backend.app.config import settings

def _base64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).decode('utf-8').rstrip('=')

def _base64url_decode(data: str) -> bytes:
    padding = '=' * (4 - (len(data) % 4))
    return base64.urlsafe_b64decode(data + padding)

def create_access_token(data: Dict[str, Any], expires_delta_seconds: Optional[int] = None) -> str:
    """Gera token JWT padrão HMAC-SHA256."""
    header = {"alg": "HS256", "typ": "JWT"}
    payload = data.copy()
    now = int(time.time())
    if expires_delta_seconds is None:
        expires_delta_seconds = settings.ACCESS_TOKEN_EXPIRE_DAYS * 86400
    payload["iat"] = now
    payload["exp"] = now + expires_delta_seconds

    header_bytes = json.dumps(header, separators=(',', ':')).encode('utf-8')
    payload_bytes = json.dumps(payload, separators=(',', ':')).encode('utf-8')

    encoded_header = _base64url_encode(header_bytes)
    encoded_payload = _base64url_encode(payload_bytes)

    signature = hmac.new(
        settings.JWT_SECRET.encode('utf-8'),
        f"{encoded_header}.{encoded_payload}".encode('utf-8'),
        hashlib.sha256
    ).digest()

    encoded_signature = _base64url_encode(signature)
    return f"{encoded_header}.{encoded_payload}.{encoded_signature}"

def decode_access_token(token: str) -> Optional[Dict[str, Any]]:
    """Decodifica e valida assinatura e expiração do JWT."""
    try:
        parts = token.split('.')
        if len(parts) != 3:
            return None
        encoded_header, encoded_payload, encoded_signature = parts

        expected_signature = hmac.new(
            settings.JWT_SECRET.encode('utf-8'),
            f"{encoded_header}.{encoded_payload}".encode('utf-8'),
            hashlib.sha256
        ).digest()

        if not hmac.compare_digest(_base64url_decode(encoded_signature), expected_signature):
            return None

        payload_bytes = _base64url_decode(encoded_payload)
        payload = json.loads(payload_bytes.decode('utf-8'))

        # Checa expiração
        if "exp" in payload and payload["exp"] < int(time.time()):
            return None

        return payload
    except Exception:
        return None
