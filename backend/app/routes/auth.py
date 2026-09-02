import datetime
import secrets
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.models import User
from backend.app.schemas.schemas import (
    UserRegister,
    UserLogin,
    UserResponse,
    TokenResponse,
    SubscriptionResponse
)
from backend.app.security.passwords import hash_password, verify_password
from backend.app.security.tokens import create_access_token
from backend.app.security.deps import get_current_user
from backend.app.services.subscription_service import SubscriptionService
from backend.app.services.analytics_service import AnalyticsService
from backend.app.config import settings

router = APIRouter(tags=["Autenticação & Assinatura"])

def generate_referral_code() -> str:
    return "CARRO" + secrets.token_hex(3).upper()

@router.post("/auth/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
def register(data: UserRegister, db: Session = Depends(get_db)):
    email_clean = data.email.strip().lower()
    existing = db.query(User).filter(User.email == email_clean).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="E-mail já cadastrado"
        )

    now = datetime.datetime.now(datetime.timezone.utc)
    trial_end = now + datetime.timedelta(days=settings.TRIAL_DAYS)
    ref_code = generate_referral_code()

    # Garante unicidade do referral_code
    while db.query(User).filter(User.referral_code == ref_code).first():
        ref_code = generate_referral_code()

    user = User(
        email=email_clean,
        password_hash=hash_password(data.password),
        trial_started_at=now,
        trial_ends_at=trial_end,
        plan="trial",
        is_active=True,
        referral_code=ref_code,
        referred_by=data.referral_code.strip() if data.referral_code else None
    )
    db.add(user)
    db.commit()
    db.refresh(user)

    AnalyticsService.track_event(db, user.id, "signup_completed", {"plan": "trial", "referred": bool(data.referral_code)})

    token = create_access_token({"sub": str(user.id), "email": user.email})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )

@router.post("/auth/login", response_model=TokenResponse)
def login(data: UserLogin, db: Session = Depends(get_db)):
    email_clean = data.email.strip().lower()
    user = db.query(User).filter(User.email == email_clean).first()
    if not user or not verify_password(data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="E-mail ou senha incorretos"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Conta inativa"
        )

    token = create_access_token({"sub": str(user.id), "email": user.email})
    return TokenResponse(
        access_token=token,
        token_type="bearer",
        user=UserResponse.model_validate(user)
    )

@router.post("/auth/logout")
def logout(current_user: User = Depends(get_current_user)):
    """Invalidação de sessão no cliente."""
    return {"status": "success", "message": "Logout realizado com sucesso"}

@router.get("/me", response_model=UserResponse)
def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.get("/subscription", response_model=SubscriptionResponse)
def get_subscription(current_user: User = Depends(get_current_user)):
    return SubscriptionService.get_subscription_status(current_user)
