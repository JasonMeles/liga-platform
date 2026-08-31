import pytest
from sqlalchemy import select
from app.models.player import Player, PlayerLeague, LeagueRoleEnum, League, PlayerLeague
from app.models.team import Team
from app.models.match import Match
from app.models.feed_item import FeedItem
from tests.conftest import auth_headers_2

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

@pytest.mark.asyncio
async def test_create_duplicate_league(client, auth_headers):
    # Arrange
    league_data = {
        "name": "Duplicate League",
        "max_teams": 10,
        "max_per_player": 2,
        "total_journeys": 5
    }

    # Act
    response1 = await client.post("/leagues/", json=league_data, headers=auth_headers)
    response2 = await client.post("/leagues/", json=league_data, headers=auth_headers)

    # Assert
    assert response1.status_code == 200
    assert response2.status_code == 400
    data = response2.json()
    assert data["detail"] == "Ce nom de ligue est déjà pris"

@pytest.mark.asyncio
async def test_create_league_unauthorized(client):
    # Arrange
    league_data = {
        "name": "Duplicate League",
        "max_teams": 10,
        "max_per_player": 2,
        "total_journeys": 5}

    # Act
    response = await client.post("/leagues/", json=league_data)  # pas de headers

    # Assert
    assert response.status_code == 401

@pytest.mark.asyncio
async def test_validate_league_not_enough_teams(client, auth_headers):
    # Arrange
    league_data = {
        "name": "Test League",
        "max_teams": 10,
        "max_per_player": 2,
        "total_journeys": 5
    }

    # Act
    response1 = await client.post("/leagues/", json=league_data, headers=auth_headers)
    league_id = response1.json()["id"]
    response2 = await client.post(f"/leagues/{league_id}/validate", headers=auth_headers)

    # Assert
    assert response1.status_code == 200
    assert response2.status_code == 400
    data = response2.json()
    assert data["detail"] == "La ligue doit avoir au moins 2 équipes"

@pytest.mark.asyncio
async def test_validate_league_not_found(client, auth_headers):
    # Act
    response = await client.post(f"/leagues/999/validate", headers=auth_headers)

    # Assert
    assert response.status_code == 403
    data = response.json()
    assert data["detail"] == "Vous n'êtes pas manager de cette ligue"

@pytest.mark.asyncio
async def test_validate_league_already_validated(client, auth_headers):
    # Arrange
    league_data = {
        "name": "Test League",
        "max_teams": 10,
        "max_per_player": 2,
        "total_journeys": 5
    }

    # Act
    response1 = await client.post("/leagues/", json=league_data, headers=auth_headers)
    league_id = response1.json()["id"]

    await client.post(f"/teams/", json={"nom": "Team1", "nom_stade": "Stade1", "id_league": league_id, "is_ia": False}, headers=auth_headers)
    await client.post(f"/teams/", json={"nom": "Team2", "nom_stade": "Stade2", "id_league": league_id, "is_ia": True}, headers=auth_headers)
    response2 = await client.post(f"/leagues/{league_id}/validate", headers=auth_headers)
    response3 = await client.post(f"/leagues/{league_id}/validate", headers=auth_headers)

    # Assert
    assert response1.status_code == 200
    assert response2.status_code == 200
    assert response3.status_code == 400
    data = response3.json()
    assert data["detail"] == "Cette ligue est déjà validée"


@pytest.mark.asyncio
async def test_delete_league(client, auth_headers, db_session, match_setup):

    # Act
    response = await client.post(f"/feed/", json={"league_id": match_setup['league_id'], "content": "Test message"}, headers=auth_headers)
    response2 = await client.delete(f"/leagues/{match_setup['league_id']}/delete", headers=auth_headers)
    response_data = await db_session.execute(select(PlayerLeague).where(PlayerLeague.league_id == match_setup['league_id']))
    playerleague = response_data.scalar_one_or_none()
    response_data2 = await db_session.execute(select(Team).where(Team.id_league == match_setup['league_id']))
    teams = response_data2.scalars().all()
    response_data3 = await db_session.execute(select(Match).where(Match.league_id == match_setup['league_id']))
    matches = response_data3.scalars().all()
    response_data4 = await db_session.execute(select(League).where(League.id == match_setup['league_id']))
    league = response_data4.scalar_one_or_none()
    response_data5 = await db_session.execute(select(FeedItem).where(FeedItem.league_id == match_setup['league_id']))
    feed_items = response_data5.scalars().all()


    # Assert
    assert response.status_code == 200
    assert response2.status_code == 200
    assert len(feed_items) == 0
    assert league is None
    assert len(matches) == 0
    assert len(teams) == 0
    assert playerleague is None

@pytest.mark.asyncio
async def test_leave_league_transfer_teams_to_ai(client, auth_headers_2, match_setup, db_session):
    # Arrange
    

    # Act
    response5 = await client.delete(f"/leagues/{match_setup['league_id']}/leave", headers=auth_headers_2)
    response_teamq = await db_session.execute(select(Team).filter(Team.id == match_setup['team2_id']))
    team2 = response_teamq.scalars().first()
    response_ai = await db_session.execute(select(Player).filter(Player.username == "AI"))
    ai_player = response_ai.scalars().first()

    assert response5.status_code == 200
    assert team2.id_owner ==  ai_player.id 