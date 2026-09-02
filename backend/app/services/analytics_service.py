import json
from sqlalchemy.orm import Session
from typing import Optional, Dict, Any
from backend.app.models.models import AnalyticsEvent

class AnalyticsService:

    @staticmethod
    def track_event(db: Session, user_id: int, event_name: str, metadata: Optional[Dict[str, Any]] = None):
        try:
            event = AnalyticsEvent(
                user_id=user_id,
                event_name=event_name,
                metadata_json=json.dumps(metadata or {})
            )
            db.add(event)
            db.commit()
        except Exception:
            # Analytics nunca deve quebrar o fluxo principal
            db.rollback()
