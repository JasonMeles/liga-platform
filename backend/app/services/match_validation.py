# backend/app/services/match_validation.py
from datetime import datetime, timedelta, timezone
from app.models.match import MatchState

CONTESTATION_DELAY = timedelta(minutes=30)

def est_contestable(match) -> bool:
    if match.state != MatchState.finished  or match.score_submitted_at is None:
        return False
    return datetime.now(timezone.utc) < match.score_submitted_at + CONTESTATION_DELAY