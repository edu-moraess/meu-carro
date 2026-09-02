from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.models import User
from backend.app.schemas.schemas import ReferralResponse
from backend.app.security.deps import get_current_user

router = APIRouter(tags=["Indicação & Crescimento"])

@router.get("/referral", response_model=ReferralResponse)
def get_referral_info(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    # Conta quantos usuários foram indicados pelo código deste usuário
    count = db.query(User).filter(User.referred_by == current_user.referral_code).count()
    share_text = f"Estou usando o Meu Carro para controlar meus gastos, abastecimentos e revisões do carro! Baixe agora e use meu código {current_user.referral_code} para 30 dias grátis."

    return ReferralResponse(
        referral_code=current_user.referral_code,
        referred_users=count,
        share_text=share_text
    )
