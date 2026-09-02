import time
from collections import defaultdict
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.models import User
from backend.app.schemas.schemas import (
    AiParseTextRequest,
    AiAnalyzeReceiptRequest,
    AiParsedData
)
from backend.app.security.deps import get_current_user
from backend.app.ai.gemini_service import GeminiService
from backend.app.services.analytics_service import AnalyticsService
from backend.app.config import settings

router = APIRouter(tags=["Inteligência Artificial (Gemini)"])

# In-memory simple rate limiter per user
user_requests = defaultdict(list)

def check_ai_rate_limit(user_id: int):
    now = time.time()
    cutoff = now - 60
    # Mantém apenas requisições do último minuto
    user_requests[user_id] = [t for t in user_requests[user_id] if t > cutoff]
    if len(user_requests[user_id]) >= settings.RATE_LIMIT_AI_PER_MINUTE:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Limite de requisições de IA atingido ({settings.RATE_LIMIT_AI_PER_MINUTE} por minuto). Aguarde alguns instantes."
        )
    user_requests[user_id].append(now)

@router.post("/ai/parse-text", response_model=AiParsedData)
def parse_text(
    data: AiParseTextRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_ai_rate_limit(current_user.id)
    
    parsed = GeminiService.parse_natural_text(data.text)
    AnalyticsService.track_event(db, current_user.id, "ai_text_parsed", {
        "text_length": len(data.text),
        "detected_type": parsed.type,
        "confidence": parsed.confidence
    })
    return parsed

@router.post("/ai/analyze-receipt", response_model=AiParsedData)
def analyze_receipt(
    data: AiAnalyzeReceiptRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    check_ai_rate_limit(current_user.id)

    if not data.receipt_text and not data.image_base64:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Informe o texto do comprovante ou a imagem codificada em base64"
        )

    parsed = GeminiService.analyze_receipt(
        receipt_text=data.receipt_text,
        image_base64=data.image_base64
    )
    AnalyticsService.track_event(db, current_user.id, "ai_receipt_analyzed", {
        "has_image": bool(data.image_base64),
        "detected_type": parsed.type,
        "confidence": parsed.confidence
    })
    return parsed
