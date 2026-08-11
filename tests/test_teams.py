import pytest
from sqlalchemy import select
from app.models.player import PlayerLeague, LeagueRoleEnum, Player
from app.models.team import Team

@pytest.mark.asyncio
async def test_claim_team(client, auth_headers, auth_headers_2, db_session):
    # Arrange
    league_data = {
        "name": "Test League",
        "max_teams": 10,
        "max_per_player": 2,
        "total_journeys": 5
    }

    team1_data = {
        "nom": "Team 1",
        "nom_stade": "Stadium 1",
        "id_league": None,  # On remplira ça après la création de la ligue
        "is_ia": True
    }

    # Act
    response = await client.post("/leagues/", json=league_data, headers=auth_headers)
    data = response.json()
    response2 =await client.post(f"/leagues/{data['id']}/join", json={}, headers=auth_headers_2)
    team1_data["id_league"] = data["id"]
    response3 = await client.post(f"/teams/", json=team1_data, headers=auth_headers)
    response4 = await client.post(f"/teams/{response3.json()['id']}/claim", json={}, headers=auth_headers_2)
    result = await db_session.execute(select(Player).filter(Player.username == "TestPlayer2"))
    player2 = result.scalars().first()
    result2 = await db_session.execute(select(Team).filter(Team.id == response3.json()['id']))
    team1 = result2.scalars().first()



    # Assert
    assert response2.status_code == 200
    assert response3.status_code == 200
    assert response4.status_code == 200
    assert team1.id_owner == player2.id


@pytest.mark.asyncio
async def test_claim_team_max_per_player(client, auth_headers, auth_headers_2, db_session):
    # Arrange
    league_data = {
        "name": "Test League",
        "max_teams": 10,
        "max_per_player": 1,
        "total_journeys": 5
    }

    team1_data = {
        "nom": "Team 1",
        "nom_stade": "Stadium 1",
        "id_league": None,  # On remplira ça après la création de la ligue
        "is_ia": True
    }

    team2_data = {
        "nom": "Team 2",
        "nom_stade": "Stadium 2",
        "id_league": None,  # On remplira ça après la création de la ligue
        "is_ia": False
    }

    # Act
    response = await client.post("/leagues/", json=league_data, headers=auth_headers)
    data = response.json()
    response2 =await client.post(f"/leagues/{data['id']}/join", json={}, headers=auth_headers_2)
    team1_data["id_league"] = data["id"]
    team2_data["id_league"] = data["id"]
    response3 = await client.post(f"/teams/", json=team1_data, headers=auth_headers)
    response4 = await client.post(f"/teams/", json=team2_data, headers=auth_headers_2)
    response5 = await client.post(f"/teams/{response3.json()['id']}/claim", json={}, headers=auth_headers_2)

    # Assert
    assert response4.status_code == 200
    assert response5.status_code == 403

@pytest.mark.asyncio
async def test_claim_team_not_in_league(client, auth_headers, auth_headers_2, db_session):
    # Arrange
    league_data = {
        "name": "Test League",
        "max_teams": 10,
        "max_per_player": 2,
        "total_journeys": 5
    }

    team1_data = {
        "nom": "Team 1",
        "nom_stade": "Stadium 1",
        "id_league": None,  # On remplira ça après la création de la ligue
        "is_ia": True
    }

    # Act
    response = await client.post("/leagues/", json=league_data, headers=auth_headers)
    data = response.json()
    team1_data["id_league"] = data["id"]
    response3 = await client.post(f"/teams/", json=team1_data, headers=auth_headers)
    response4 = await client.post(f"/teams/{response3.json()['id']}/claim", json={}, headers=auth_headers_2)

    # Assert
    assert response3.status_code == 200
    assert response4.status_code == 403


@pytest.mark.asyncio
async def test_claim_team_already_taken(client, auth_headers, auth_headers_2, db_session):
    # Arrange
    league_data = {
        "name": "Test League",
        "max_teams": 10,
        "max_per_player": 2,
        "total_journeys": 5
    }

    team1_data = {
        "nom": "Team 1",
        "nom_stade": "Stadium 1",
        "id_league": None,  # On remplira ça après la création de la ligue
        "is_ia": True
    }

    # Act
    response = await client.post("/leagues/", json=league_data, headers=auth_headers)
    data = response.json()
    team1_data["id_league"] = data["id"]
    response3 = await client.post(f"/teams/", json=team1_data, headers=auth_headers)
    response2 =await client.post(f"/leagues/{data['id']}/join", json={}, headers=auth_headers_2)
    response4 = await client.post(f"/teams/{response3.json()['id']}/claim", json={}, headers=auth_headers_2)
    response5 = await client.post(f"/teams/{response3.json()['id']}/claim", json={}, headers=auth_headers)

    # Assert
    assert response3.status_code == 200
    assert response4.status_code == 200
    assert response5.status_code == 403