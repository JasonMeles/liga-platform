# backend/tests/test_match_validation.py
from datetime import datetime, timedelta, timezone
from types import SimpleNamespace
from app.models.match import MatchState
from app.services.match_validation import est_contestable


def test_contestable_dans_le_delai():
    # Arrange
    match = SimpleNamespace(
        state=MatchState.finished,
        score_submitted_at=datetime.now(timezone.utc) - timedelta(minutes=10),
    )
    # Act + Assert
    assert est_contestable(match) is True

def test_non_contestable_hors_le_delai():
    # Arrange
    match = SimpleNamespace(
        state=MatchState.finished,
        score_submitted_at=datetime.now(timezone.utc) - timedelta(minutes=40),
    )
    # Act + Assert
    assert est_contestable(match) is False

def test_non_contestable_match_simule():
    # Arrange
    match = SimpleNamespace(
        state=MatchState.finished,
        score_submitted_at=None,
    )
    # Act + Assert
    assert est_contestable(match) is False

def test_non_contestable_match_en_cours():
    # Arrange
    match = SimpleNamespace(
        state=MatchState.in_progress,
        score_submitted_at=datetime.now(timezone.utc) - timedelta(minutes=10)
    )
    # Act + Assert
    assert est_contestable(match) is False