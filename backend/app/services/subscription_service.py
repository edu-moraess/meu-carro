import datetime
import math
from backend.app.models.models import User
from backend.app.schemas.schemas import SubscriptionResponse

class SubscriptionService:

    @staticmethod
    def get_subscription_status(user: User) -> SubscriptionResponse:
        now = datetime.datetime.now(datetime.timezone.utc)
        trial_end = user.trial_ends_at
        if trial_end.tzinfo is None:
            trial_end = trial_end.replace(tzinfo=datetime.timezone.utc)

        total_secs = (trial_end - now).total_seconds()
        days_remaining = max(0, int(math.ceil(total_secs / 86400.0))) if total_secs > 0 else 0
        is_active = (total_secs > 0) or (user.plan == "premium")

        warning_message = None
        if user.plan == "trial":
            if days_remaining <= 1 and is_active:
                warning_message = "Atenção: Seu período de teste gratuito termina em 1 dia!"
            elif days_remaining <= 3 and is_active:
                warning_message = f"Seu período de teste gratuito termina em {days_remaining} dias."
            elif days_remaining <= 7 and is_active:
                warning_message = f"Lembrete: Restam {days_remaining} dias do seu período de teste."

        return SubscriptionResponse(
            plan=user.plan,
            trial_active=is_active,
            trial_days_remaining=days_remaining,
            trial_ends_at=trial_end,
            warning_message=warning_message
        )
