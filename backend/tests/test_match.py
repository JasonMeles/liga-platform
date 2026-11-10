import pytest
from sqlalchemy import select
from app.models.player import PlayerLeague, LeagueRoleEnum
from app.models.match import Match, MatchState
from app.models.feed_item import FeedItem, MessageTypeEnum
from datetime import datetime, timezone, timedelta
from app.services.match_validation import CONTESTATION_DELAY
import random

async def ligue_lancee(client, headers_manager, equipes, sport_type="football", headers_membres=()):
    """Crée une ligue, inscrit les équipes, la lance et renvoie l'id du premier match.
    equipes : liste de (headers du propriétaire, is_ia)"""
    league_data = {
        "name": "Ligue Simu",
        "max_teams": len(equipes),
        "max_per_player": len(equipes),
        "total_journeys": 2,
        "sport_type": sport_type,
    }
    league = (await client.post("/leagues/", json=league_data, headers=headers_manager)).json()
    for headers in headers_membres:
        await client.post("/leagues/join", json={"invite_code": league["invite_code"]}, headers=headers)
    for i, (headers, is_ia) in enumerate(equipes):
        await client.post("/teams/", json={
            "nom": f"Team {i + 1}", "nom_stade": f"Stade {i + 1}",
            "id_league": league["id"], "is_ia": is_ia,
        }, headers=headers)
    await client.post(f"/leagues/{league['id']}/validate", json={}, headers=headers_manager)
    calendar = (await client.get(f"/leagues/{league['id']}/calendar", headers=headers_manager)).json()
    return calendar[0]["id"]

async def creer_joueur(client, username):
    """Inscrit et connecte un joueur, renvoie ses headers d'authentification."""
    password = "SuperMotDePasse12345"
    await client.post("/auth/register", json={
        "username": username, "email": f"{username.lower()}@example.com", "password": password})
    login = await client.post("/auth/login", data={"username": username, "password": password})
    return {"Authorization": f"Bearer {login.json()['access_token']}"}

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
    response3 = await client.post(f"/leagues/join", json={"invite_code": match_setup["invite_code"]}, headers=auth_headers_3)

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
    assert "contestable" in data["message"]
    assert match.state == MatchState.finished
    assert match.score_submitted_at is not None
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
    assert "contestable" in data["message"]
    assert match.state == MatchState.finished
    assert match.score_submitted_at is not None
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
        "sport_type": "football",
    }   

    response5 = await client.post("/leagues/", json=league_data, headers=auth_headers)
    response6 = await client.post("/leagues/join", json={"invite_code": response5.json()["invite_code"]}, headers=auth_headers_2)
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
    assert "contestable" in data["message"]
    assert match.state == MatchState.finished
    assert match.score_submitted_at is not None
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
    response3 = await client.post("/leagues/join", json={"invite_code": match_setup["invite_code"]}, headers=auth_headers_3)

    # Act — on démarre le match avec le propriétaire de l'équipe à domicile
    await client.put(f"/matches/{match_id}/start", headers=auth_headers)

    # Act — on tente de mettre à jour le score avec un joueur qui n'est pas propriétaire de l'équipe et pas manager
    response = await client.put(f"/matches/{match_id}/score", json=score_data, headers=auth_headers_3)

    # Assert
    assert response.status_code == 400
    data = response.json()
    assert "Vous ne controlez aucune de ces équipes et vous n'êtes pas manager de la ligue" in data["detail"]

@pytest.mark.asyncio
async def test_score_creates_feed_event(client, auth_headers, match_setup, db_session):
    # Arrange
    match_id = match_setup["match_id1"]
    score_data = {
        "home_score": 1,
        "away_score": 0
    }

    # Act — on démarre le match
    await client.put(f"/matches/{match_id}/start", headers=auth_headers)
    response = await client.put(f"/matches/{match_id}/score", json=score_data, headers=auth_headers)

    # Act — on vérifie le feed et l’état en base
    result = await db_session.execute(
    select(FeedItem).filter(FeedItem.match_id == match_id)
    )
    feed_item = result.scalars().first()
    
    match = await db_session.execute(select(Match).filter(Match.id == match_id))
    match = match.scalars().first()

    # Assert
    assert feed_item is not None
    assert feed_item.type == MessageTypeEnum.match_event
    assert match.state == MatchState.finished


@pytest.mark.asyncio
async def test_score_already_finished(client, auth_headers, match_setup, db_session):
    # Arrange
    match_id = match_setup["match_id1"]
    vrai_score = {"home_score": 2, "away_score": 1}
    score_triche = {"home_score": 0, "away_score": 3}

    # Act — on démarre le match et on saisit le vrai score (le match passe à finished)
    await client.put(f"/matches/{match_id}/start", headers=auth_headers)
    response1 = await client.put(f"/matches/{match_id}/score", json=vrai_score, headers=auth_headers)

    # Act — on tente de ressaisir un autre score sur le match déjà terminé
    response2 = await client.put(f"/matches/{match_id}/score", json=score_triche, headers=auth_headers)

    # On relit le match en base
    result = await db_session.execute(select(Match).filter(Match.id == match_id))
    match = result.scalars().first()

    # Assert — la première saisie a réussi
    assert response1.status_code == 200

    # Assert — la deuxième est refusée
    assert response2.status_code == 400
    assert "Le match n'est pas en cours" in response2.json()["detail"]

    # Assert — la base a gardé le vrai score
    assert match.score_home == 2
    assert match.score_away == 1


@pytest.mark.asyncio
async def test_simulate_basket_no_draw(client, auth_headers, db_session, monkeypatch):
    # Arrange — ligue de basket IA vs IA, tirage truqué : toujours 100
    match_id = await ligue_lancee(client, auth_headers,
                                  [(auth_headers, True), (auth_headers, True)],
                                  sport_type="basketball")
    monkeypatch.setattr(random, "randint", lambda a, b: 100)

    # Act
    response = await client.put(f"/matches/{match_id}/simulate", headers=auth_headers)
    result = await db_session.execute(select(Match).filter(Match.id == match_id))
    match = result.scalars().first()

    # Assert — l'égalité a été cassée : une équipe a 100, l'autre 101
    assert response.status_code == 200
    assert {match.score_home, match.score_away} == {100, 101}
    assert match.state == MatchState.finished
    assert match.score_submitted_at is None

@pytest.mark.asyncio
async def test_simulate_two_humans_is_contestable(client, auth_headers, auth_headers_2, db_session):
    # Arrange — ligue de football, deux humains différents
    match_id = await ligue_lancee(client, auth_headers,
                                  [(auth_headers, False), (auth_headers_2, False)],
                                  headers_membres=[auth_headers_2])

    # Act
    response = await client.put(f"/matches/{match_id}/simulate", headers=auth_headers)
    result = await db_session.execute(select(Match).filter(Match.id == match_id))
    match = result.scalars().first()

    # Assert
    assert response.status_code == 200
    assert match.state == MatchState.finished
    assert 0 <= match.score_home <= 5
    assert 0 <= match.score_away <= 5
    assert match.score_submitted_at is not None   # deux humains → contestable

@pytest.mark.asyncio
async def test_simulate_already_finished(client, auth_headers, db_session, monkeypatch):
    # Arrange — ligue IA vs IA, premier tirage truqué à 1
    match_id = await ligue_lancee(client, auth_headers,
                                  [(auth_headers, True), (auth_headers, True)])
    monkeypatch.setattr(random, "randint", lambda a, b: 1)

    # Act — première simulation (acceptée), puis tentative de relance avec un tirage à 4
    response1 = await client.put(f"/matches/{match_id}/simulate", headers=auth_headers)
    monkeypatch.setattr(random, "randint", lambda a, b: 4)
    response2 = await client.put(f"/matches/{match_id}/simulate", headers=auth_headers)

    # Lecture en base une seule fois, à la fin (évite le cache de db_session)
    result = await db_session.execute(select(Match).filter(Match.id == match_id))
    match = result.scalars().first()

    # Assert — la relance est refusée et le premier score est conservé
    assert response1.status_code == 200
    assert response2.status_code == 400
    assert match.score_home == 1
    assert match.score_away == 1


@pytest.mark.asyncio
async def test_simulate_unauthorized(client, auth_headers, auth_headers_2, db_session):
    # Arrange — humain vs IA : le manager (joueur 1) crée l'IA, le joueur 2 son équipe
    match_id = await ligue_lancee(client, auth_headers,
                                  [(auth_headers, True), (auth_headers_2, False)],
                                  headers_membres=[auth_headers_2])

    # Act — le manager tente de simuler à la place du joueur humain
    response = await client.put(f"/matches/{match_id}/simulate", headers=auth_headers)
    result = await db_session.execute(select(Match).filter(Match.id == match_id))
    match = result.scalars().first()

    # Assert — refusé, le match n'a pas bougé
    assert response.status_code == 403
    assert match.state == MatchState.pending
    assert match.score_submitted_at is None

@pytest.mark.asyncio
async def test_contest_match_ok(client, auth_headers, auth_headers_2, db_session):
    # Arrange — ligue de football, deux humains différents
    match_id = await ligue_lancee(client, auth_headers,
                                  [(auth_headers, False), (auth_headers_2, False)],
                                  headers_membres=[auth_headers_2])
    
    await client.put(f"/matches/{match_id}/start", headers=auth_headers)
    r = await client.put(f"/matches/{match_id}/score", json={"home_score": 2, "away_score": 1}, headers=auth_headers)
    assert r.status_code == 200
    
    # Act — on conteste le match avec le joueur 2
    response = await client.put(f"/matches/{match_id}/contest", headers=auth_headers_2)
    result = await db_session.execute(select(Match).filter(Match.id == match_id))
    response2 = await db_session.execute(select(FeedItem).filter(FeedItem.match_id == match_id))
    feeds = response2.scalars().all()
    match = result.scalars().first()

    # Assert — le match est repassé à contesté et un feed a été créé
    assert response.status_code == 200
    assert match.state == MatchState.contested
    assert any("contesté par" in f.content for f in feeds)
    assert (match.score_home, match.score_away) == (2, 1)

@pytest.mark.asyncio
async def test_contest_unauthorized(client, auth_headers, auth_headers_2, db_session):
    # Arrange — ligue de football, deux humains différents Charlie, troisième joueur (sera spectateur)
    charlie_headers = await creer_joueur(client, "Charlie")
    match_id = await ligue_lancee(client, auth_headers,
                                  [(auth_headers, False), (auth_headers_2, False)],
                                  headers_membres=[auth_headers_2, charlie_headers])
    
    await client.put(f"/matches/{match_id}/start", headers=auth_headers)
    r = await client.put(f"/matches/{match_id}/score", json={"home_score": 2, "away_score": 1}, headers=auth_headers)
    assert r.status_code == 200

    # Act — on tente de contester le match avec un joueur qui n'est pas propriétaire de l'équipe
    response = await client.put(f"/matches/{match_id}/contest", headers=charlie_headers)
    result = await db_session.execute(select(Match).filter(Match.id == match_id))
    match = result.scalars().first()  

    # Assert — le match n'a pas été contesté
    assert response.status_code == 403
    assert match.state == MatchState.finished

@pytest.mark.asyncio
async def test_contest_simulated_match(client, auth_headers, auth_headers_2, db_session):
    #  Arrange — humain vs IA : le joueur 2 simule (non contestable)
    match_id = await ligue_lancee(client, auth_headers,
                                  [(auth_headers, True), (auth_headers_2, False)],
                                  headers_membres=[auth_headers_2])
    
    r = await client.put(f"/matches/{match_id}/simulate", headers=auth_headers_2)
    assert r.status_code == 200

    # Act — on tente de contester le match avec le joueur 2
    response = await client.put(f"/matches/{match_id}/contest", headers=auth_headers_2)
    result = await db_session.execute(select(Match).filter(Match.id == match_id))
    match = result.scalars().first()

    # Assert — refusé : un match simulé contre l'IA n'est pas contestable
    assert response.status_code == 400
    assert match.state == MatchState.finished

@pytest.mark.asyncio
async def test_contest_after_delay(client, auth_headers, auth_headers_2, db_session):
    # Arrange — ligue de football, deux humains différents
    match_id = await ligue_lancee(client, auth_headers,
                                  [(auth_headers, False), (auth_headers_2, False)],
                                  headers_membres=[auth_headers_2])
    
    await client.put(f"/matches/{match_id}/start", headers=auth_headers)
    r = await client.put(f"/matches/{match_id}/score", json={"home_score": 2, "away_score": 1}, headers=auth_headers)
    assert r.status_code == 200

    # On modifie la date de soumission du score pour simuler un dépassement du délai de contestation
    result = await db_session.execute(select(Match).filter(Match.id == match_id))
    match = result.scalars().first()
    match.score_submitted_at = datetime.now(timezone.utc) - CONTESTATION_DELAY - timedelta(minutes=1)
    await db_session.commit()

    # Act — on tente de contester le match avec le joueur 2 après le délai
    response = await client.put(f"/matches/{match_id}/contest", headers=auth_headers_2)
    result = await db_session.execute(select(Match).filter(Match.id == match_id))
    match = result.scalars().first()

    # Assert — refusé : le délai de contestation est dépassé
    assert response.status_code == 400
    assert "n'est pas contestable" in response.json()["detail"]
    assert match.state == MatchState.finished

@pytest.mark.asyncio
async def test_contest_twice(client, auth_headers, auth_headers_2, db_session):
    # Arrange — ligue de football, deux humains différents
    match_id = await ligue_lancee(client, auth_headers,
                                  [(auth_headers, False), (auth_headers_2, False)],
                                  headers_membres=[auth_headers_2])
    
    await client.put(f"/matches/{match_id}/start", headers=auth_headers)
    r = await client.put(f"/matches/{match_id}/score", json={"home_score": 2, "away_score": 1}, headers=auth_headers)
    assert r.status_code == 200

    #Arrange — on conteste le match avec le joueur 2 une première fois
    response1 = await client.put(f"/matches/{match_id}/contest", headers=auth_headers_2)
    assert response1.status_code == 200

    # Act — on tente de contester le match une deuxième fois avec le même joueur
    response2 = await client.put(f"/matches/{match_id}/contest", headers=auth_headers_2)
    result2 = await db_session.execute(select(Match).filter(Match.id == match_id))
    match1 = result2.scalars().first()
    feeds = (await db_session.execute(select(FeedItem).filter(FeedItem.match_id == match_id))).scalars().all()

    # Assert — la deuxième contestation est refusée car le match est déjà contesté
    assert response2.status_code == 400
    assert "n'est pas contestable" in response2.json()["detail"]
    assert sum("contesté par" in f.content for f in feeds) == 1
    assert match1.state == MatchState.contested

@pytest.mark.asyncio
async def test_resolve_match_ok(client, auth_headers, auth_headers_2, db_session):
    # Arrange — ligue de football, deux humains différents
    match_id = await ligue_lancee(client, auth_headers,
                                  [(auth_headers, False), (auth_headers_2, False)],
                                  headers_membres=[auth_headers_2])
    
    await client.put(f"/matches/{match_id}/start", headers=auth_headers)
    r = await client.put(f"/matches/{match_id}/score", json={"home_score": 2, "away_score": 1}, headers=auth_headers)
    assert r.status_code == 200

    # Arrange — on conteste le match avec le joueur 2
    response1 = await client.put(f"/matches/{match_id}/contest", headers=auth_headers_2)
    assert response1.status_code == 200

    # Act — on résout le match avec le manager (joueur 1)
    response2 = await client.put(f"/matches/{match_id}/resolve", json={"home_score": 3, "away_score": 0}, headers=auth_headers)
    result = await db_session.execute(select(Match).filter(Match.id == match_id))
    match = result.scalars().first()
    feeds = (await db_session.execute(select(FeedItem).filter(FeedItem.match_id == match_id))).scalars().all()

    # Assert — le match est repassé à finished et le score a été mis à jour
    assert response2.status_code == 200
    assert match.state == MatchState.finished
    assert (match.score_home, match.score_away) == (3, 0)
    assert match.score_submitted_at is None
    assert any("résolue par" in f.content for f in feeds)

@pytest.mark.asyncio
async def test_resolve_match_unauthorized(client, auth_headers, auth_headers_2, db_session):
    # Arrange — ligue de football, deux humains différents
    match_id = await ligue_lancee(client, auth_headers,
                                  [(auth_headers, False), (auth_headers_2, False)],
                                  headers_membres=[auth_headers_2])
    
    await client.put(f"/matches/{match_id}/start", headers=auth_headers)
    r = await client.put(f"/matches/{match_id}/score", json={"home_score": 2, "away_score": 1}, headers=auth_headers)
    assert r.status_code == 200

    # Arrange — on conteste le match avec le joueur 2
    response1 = await client.put(f"/matches/{match_id}/contest", headers=auth_headers_2)
    assert response1.status_code == 200

    # Act — on tente de résoudre le match avec le joueur 2 (non manager)
    response2 = await client.put(f"/matches/{match_id}/resolve", json={"home_score": 3, "away_score": 0}, headers=auth_headers_2)
    result = await db_session.execute(select(Match).filter(Match.id == match_id))
    match = result.scalars().first()

    # Assert — refusé : seul le manager peut résoudre un match contesté
    assert response2.status_code == 403
    assert match.state == MatchState.contested
    assert "Vous n'êtes pas manager de la ligue pour ce match" in response2.json()["detail"]
    assert (match.score_home, match.score_away) == (2, 1)

@pytest.mark.asyncio
async def test_resolve_match_not_contested(client, auth_headers, auth_headers_2, db_session):
    # Arrange — ligue de football, deux humains différents
    match_id = await ligue_lancee(client, auth_headers,
                                  [(auth_headers, False), (auth_headers_2, False)],
                                  headers_membres=[auth_headers_2])
    
    await client.put(f"/matches/{match_id}/start", headers=auth_headers)
    r = await client.put(f"/matches/{match_id}/score", json={"home_score": 2, "away_score": 1}, headers=auth_headers)
    assert r.status_code == 200

    # Act — on tente de résoudre le match avec le manager alors qu'il n'est pas contesté
    response2 = await client.put(f"/matches/{match_id}/resolve", json={"home_score": 3, "away_score": 0}, headers=auth_headers)
    result = await db_session.execute(select(Match).filter(Match.id == match_id))
    match = result.scalars().first()

    # Assert — refusé : le match n'est pas contesté
    assert response2.status_code == 400
    assert match.state == MatchState.finished
    assert "n'est pas contesté" in response2.json()["detail"]
    assert (match.score_home, match.score_away) == (2, 1)

@pytest.mark.asyncio
async def test_contest_after_resolve(client, auth_headers, auth_headers_2, db_session):
    # Arrange — ligue de football, deux humains différents
    match_id = await ligue_lancee(client, auth_headers,
                                  [(auth_headers, False), (auth_headers_2, False)],
                                  headers_membres=[auth_headers_2])
    
    await client.put(f"/matches/{match_id}/start", headers=auth_headers)
    r = await client.put(f"/matches/{match_id}/score", json={"home_score": 2, "away_score": 1}, headers=auth_headers)
    assert r.status_code == 200

    # Arrange — on conteste le match avec le joueur 2
    response1 = await client.put(f"/matches/{match_id}/contest", headers=auth_headers_2)
    assert response1.status_code == 200

    # Arrange — on résout le match avec le manager (joueur 1)
    response2 = await client.put(f"/matches/{match_id}/resolve", json={"home_score": 3, "away_score": 0}, headers=auth_headers)
    assert response2.status_code == 200

    # Act — on tente de contester le match après résolution
    response3 = await client.put(f"/matches/{match_id}/contest", headers=auth_headers_2)
    result = await db_session.execute(select(Match).filter(Match.id == match_id))
    match = result.scalars().first()
    feeds = (await db_session.execute(select(FeedItem).filter(FeedItem.match_id == match_id))).scalars().all()
    

    # Assert — refusé : le match n'est plus contestable après résolution
    assert response3.status_code == 400
    assert "n'est pas contestable" in response3.json()["detail"]
    assert match.state == MatchState.finished
    assert (match.score_home, match.score_away) == (3, 0)              # la décision du manager reste intacte
    assert sum("contesté par" in f.content for f in feeds) == 1        # la tentative n'a rien écrit