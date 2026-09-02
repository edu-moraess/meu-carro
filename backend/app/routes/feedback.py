from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session
from backend.app.database import get_db
from backend.app.models.models import User, Feedback
from backend.app.schemas.schemas import FeedbackCreate, FeedbackResponse
from backend.app.security.deps import get_current_user
from backend.app.services.analytics_service import AnalyticsService

router = APIRouter(tags=["Feedback"])

@router.post("/feedback", response_model=FeedbackResponse, status_code=status.HTTP_201_CREATED)
def submit_feedback(
    data: FeedbackCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    feedback = Feedback(
        user_id=current_user.id,
        rating=data.rating,
        message=data.message.strip()
    )
    db.add(feedback)
    db.commit()
    db.refresh(feedback)

    AnalyticsService.track_event(db, current_user.id, "feedback_submitted", {
        "rating": feedback.rating,
        "message_length": len(feedback.message)
    })

    return FeedbackResponse(
        id=feedback.id,
        status="success",
        message="Obrigado pelo seu feedback! Ele é essencial para o aprimoramento contínuo do Meu Carro."
    )
