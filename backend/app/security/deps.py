try:
    from fastapi import Depends, HTTPException, status
    from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
except ImportError:
    class HTTPException(Exception):
        def __init__(self, status_code: int, detail: str, headers=None):
            self.status_code = status_code
            self.detail = detail
            self.headers = headers
            super().__init__(detail)

    class status:
        HTTP_400_BAD_REQUEST = 400
        HTTP_401_UNAUTHORIZED = 401
        HTTP_403_FORBIDDEN = 403
        HTTP_404_NOT_FOUND = 404
        HTTP_429_TOO_MANY_REQUESTS = 429

    def Depends(dependency=None, use_cache=True):
        return dependency

    class HTTPBearer:
        pass

    class HTTPAuthorizationCredentials:
        def __init__(self, credentials: str = ""):
            self.credentials = credentials

import datetime
from backend.app.database import get_db
from backend.app.models.models import User, Vehicle
from backend.app.security.tokens import decode_access_token

security = HTTPBearer()

def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db = Depends(get_db)
) -> User:
    token = credentials.credentials if hasattr(credentials, "credentials") else str(credentials)
    payload = decode_access_token(token)
    if not payload or "sub" not in payload:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token inválido ou expirado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    user_id = payload["sub"]
    try:
        user_id = int(user_id)
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token com identificador inválido",
            headers={"WWW-Authenticate": "Bearer"},
        )

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Usuário não encontrado",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Usuário inativo"
        )

    return user

def get_user_vehicle_or_404(
    vehicle_id: int,
    current_user: User,
    db
) -> Vehicle:
    """Garante estritamente que o veículo pertence ao usuário autenticado."""
    vehicle = db.query(Vehicle).filter(
        Vehicle.id == vehicle_id,
        Vehicle.user_id == current_user.id
    ).first()

    if not vehicle:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Veículo não encontrado ou não pertence ao usuário autenticado"
        )
    return vehicle
