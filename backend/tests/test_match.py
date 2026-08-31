import pytest
from sqlalchemy import select
from app.models.player import PlayerLeague, LeagueRoleEnum
from app.models.match import Match, MatchState


@pytest.mark.asyncio
async def test_start_match_success(client, auth_headers, match_setup):
    # Arrange
    match_id = match_setup["match_id1"]

    # Act
    response = await client.put(f"/matches/{match_id}/start", headers=auth_headers)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert data["message"] == "Le match a commencé"


@pytest.mark.asyncio
async def test_start_match_already_started(client, auth_headers, match_setup, db_session):
    # Arrange
    match_id = match_setup["match_id1"]

    # Act — on démarre le match une première fois
    await client.put(f"/matches/{match_id}/start", headers=auth_headers)

    # Act — on tente de démarrer le match une deuxième fois
    response = await client.put(f"/matches/{match_id}/start", headers=auth_headers)
    response2 = await db_session.execute(select(Match).filter(Match.id == match_id))
    match = response2.scalars().first()

    # Assert
    assert response.status_code == 400
    data = response.json()
    assert "Le match a déjà commencé" in data["detail"]
    assert match.state == MatchState.in_progress

@pytest.mark.asyncio
async def test_start_match_unauthorized(client, match_setup):
    # Arrange
    match_id = match_setup["match_id1"]
    player_data = {
        "username": "TestPlayer3",
        "email": "testplayer3@example.com",
        "password": "SuperMotDePasse12345"
    }

    login_data = {
        "username": "TestPlayer3",
        "password": "SuperMotDePasse12345"
    }


    # Act — on tente de démarrer le match avec un joueur qui n'est pas propriétaire de l'équipe
    response1 = await client.post("/auth/register", json=player_data)
    response2 = await client.post("/auth/login", data=login_data)
    auth_headers_3 = {"Authorization": f"Bearer {response2.json()['access_token']}"}
    response3 = await client.post(f"/leagues/{match_setup['league_id']}/join", json={}, headers=auth_headers_3)

    response = await client.put(f"/matches/{match_id}/start", headers=auth_headers_3)


    # Assert
    assert response.status_code == 400
    data = response.json()
    assert "Vous ne controlez aucune de ces équipes" in data["detail"]

@pytest.mark.asyncio
async def test_score_by_team_home_owner(client, auth_headers, match_setup, db_session):
    # Arrange
    match_id = match_setup["match_id1"]
    score_data = {
        "home_score": 2,
        "away_score": 1
    }

    # Act
    response = await client.put(f"/matches/{match_id}/start", headers=auth_headers)
    response2 = await client.put(f"/matches/{match_id}/score", json=score_data, headers=auth_headers)
    match = await db_session.execute(select(Match).filter(Match.id == match_id))
    match = match.scalars().first()



    # Assert
    assert response2.status_code == 200
    data = response2.json()
    assert data["message"] == "Score mis à jour"
    assert match.score_home == 2
    assert match.score_away == 1

@pytest.mark.asyncio
async def test_score_by_team_away_owner(client, auth_headers_2, match_setup, db_session):
    # Arrange
    match_id = match_setup["match_id1"]
    score_data = {
        "home_score": 3,
        "away_score": 2
    }

    # Act
    response = await client.put(f"/matches/{match_id}/start", headers=auth_headers_2)
    response2 = await client.put(f"/matches/{match_id}/score", json=score_data, headers=auth_headers_2)
    match = await db_session.execute(select(Match).filter(Match.id == match_id))
    match = match.scalars().first()

    # Assert
    assert response2.status_code == 200
    data = response2.json()
    assert data["message"] == "Score mis à jour"
    assert match.score_home == 3
    assert match.score_away == 2

@pytest.mark.asyncio
async def test_score_by_manager(client, auth_headers, auth_headers_2, db_session):
    # Arrange
    league_data = {
        "name": "Test League",
        "max_teams": 2,
        "max_per_player": 1,
        "total_journeys": 2,
        "sport_type": "football"
    }   

    response5 = await client.post("/leagues/", json=league_data, headers=auth_headers)
    response6 = await client.post(f"/leagues/{response5.json()['id']}/join", json={}, headers=auth_headers_2)
    response7 = await client.post(f"/teams/", json={"nom": "Team 1", "nom_stade": "Stadium 1", "id_league": response5.json()['id'], "is_ia": True}, headers=auth_headers)
    response8 = await client.post(f"/teams/", json={"nom": "Team 2", "nom_stade": "Stadium 2", "id_league": response5.json()['id'], "is_ia": False}, headers=auth_headers_2)
    response9 = await client.post(f"/leagues/{response5.json()['id']}/validate", json={}, headers=auth_headers)
    response10 = await client.get(f"/leagues/{response5.json()['id']}/calendar", headers=auth_headers)

    calendar = response10.json()
    match_id = calendar[0]["id"]

    score_data = {
        "home_score": 1,
        "away_score": 0 
    }   

    # Act
    response = await client.put(f"/matches/{match_id}/start", headers=auth_headers_2)
    response2 = await client.put(f"/matches/{match_id}/score", json=score_data, headers=auth_headers)
    match = await db_session.execute(select(Match).filter(Match.id == match_id))
    match = match.scalars().first()    

    # Assert
    assert response2.status_code == 200
    data = response2.json()
    assert data["message"] == "Score mis à jour"
    assert match.score_home == 1
    assert match.score_away == 0   

@pytest.mark.asyncio
async def test_score_match_not_in_progress(client, auth_headers, match_setup):
    # Arrange
    match_id = match_setup["match_id1"]
    score_data = {
        "home_score": 1,
        "away_score": 0
    }

    # Act — on tente de mettre à jour le score d'un match qui n'a pas commencé
    response = await client.put(f"/matches/{match_id}/score", json=score_data, headers=auth_headers)

    # Assert
    assert response.status_code == 400
    data = response.json()
    assert "Le match n'est pas en cours" in data["detail"]


@pytest.mark.asyncio
async def test_score_unauthorized(client, auth_headers, auth_headers_2, match_setup):
    # Arrange
    match_id = match_setup["match_id1"]
    score_data = {
        "home_score": 1,
        "away_score": 0
    }

    player_data = {
        "username": "TestPlayer3",
        "email": "testplayer3@example.com",
        "password": "SuperMotDePasse12345"
    }

    login_data = {
        "username": "TestPlayer3",
        "password": "SuperMotDePasse12345"
    }

    # Act — on enregistre un nouveau joueur
    response1 = await client.post("/auth/register", json=player_data)
    response2 = await client.post("/auth/login", data=login_data)
    auth_headers_3 = {"Authorization": f"Bearer {response2.json()['access_token']}"}
    response3 = await client.post(f"/leagues/{match_setup['league_id']}/join", json={}, headers=auth_headers_3)

    # Act — on démarre le match avec le propriétaire de l'équipe à domicile
    await client.put(f"/matches/{match_id}/start", headers=auth_headers)

    # Act — on tente de mettre à jour le score avec un joueur qui n'est pas propriétaire de l'équipe et pas manager
    response = await client.put(f"/matches/{match_id}/score", json=score_data, headers=auth_headers_3)

    # Assert
    assert response.status_code == 400
    data = response.json()
    assert "Vous ne controlez aucune de ces équipes et vous n'êtes pas manager de la ligue" in data["detail"]

@pytest.mark.asyncio
async def test_finish_match_success(client, auth_headers, match_setup, db_session):
    # Arrange
    match_id = match_setup["match_id1"]
    score_data = {
        "home_score": 1,
        "away_score": 0
    }

    # Act — on démarre le match
    await client.put(f"/matches/{match_id}/start", headers=auth_headers)
    response = await client.put(f"/matches/{match_id}/score", json=score_data, headers=auth_headers)

    # Act — on termine le match
    response2 = await client.put(f"/matches/{match_id}/finish", headers=auth_headers)
    match = await db_session.execute(select(Match).filter(Match.id == match_id))
    match = match.scalars().first()

    # Assert
    assert response2.status_code == 200
    data = response2.json()
    assert data["message"] == "Le match est terminé"
    assert match.state == MatchState.finished

@pytest.mark.asyncio
async def test_finish_match_no_score(client, auth_headers, match_setup):
    # Arrange
    match_id = match_setup["match_id1"]

    # Act — on démarre le match
    await client.put(f"/matches/{match_id}/start", headers=auth_headers)

    # Act — on tente de terminer le match sans avoir mis à jour le score
    response = await client.put(f"/matches/{match_id}/finish", headers=auth_headers)

    # Assert
    assert response.status_code == 400
    data = response.json()
    assert "Le score doit être défini pour terminer le match" in data["detail"]


@pytest.mark.asyncio
async def test_finish_match_not_in_progress(client, auth_headers, match_setup):
    # Arrange
    match_id = match_setup["match_id1"]

    # Act — on tente de terminer le match sans l'avoir démarré
    response = await client.put(f"/matches/{match_id}/finish", headers=auth_headers)

    # Assert
    assert response.status_code == 400
    data = response.json()
    assert "Le match n'est pas en cours" in data["detail"]


