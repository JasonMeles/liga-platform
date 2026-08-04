import pytest
from sqlalchemy import select
from app.models.player import PlayerLeague, LeagueRoleEnum

@pytest.mark.asyncio
async def test_create_league(client, auth_headers, db_session):
    # Arrange
    league_data = {
        "name": "Test League",
        "max_teams": 10,
        "max_per_player": 2,
        "total_journeys": 5
    }

    # Act
    response = await client.post("/leagues/", json=league_data, headers=auth_headers)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "id" in data
    assert "is_active" in data
    assert data["name"] == league_data["name"]
    assert data["manager_username"] == "TestPlayer1"

    result = await db_session.execute(select(PlayerLeague).where(PlayerLeague.league_id == data["id"]))
    players = result.scalar_one_or_none()
    assert players is not None
    assert players.role == LeagueRoleEnum.manager
