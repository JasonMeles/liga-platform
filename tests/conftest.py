import pytest
import pytest_asyncio
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool
from httpx import AsyncClient, ASGITransport
import os
from dotenv import load_dotenv
from app.main import app

from app.database.connection import Base, get_db
# On importe tous les modèles pour que Base les "connaisse" tous
from app.models import feed_item, match, player, team # adapte selon tes vrais noms de fichiers

from fastapi.testclient import TestClient

load_dotenv()

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")


test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
TestSessionLocal = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)
ws_test_client = TestClient(app)


@pytest_asyncio.fixture
async def db_session():
    # Setup : créer toutes les tables
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # On donne une session au test
    async with TestSessionLocal() as session:
        yield session

    # Teardown : tout supprimer
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client(db_session, monkeypatch):
    # On remplace get_db par une version qui utilise la session de test
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    monkeypatch.setattr("app.main.get_db", override_get_db)
    async with app.router.lifespan_context(app):
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            yield ac

    app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_headers(client):
    # Arrange
    player_data = {
        "username": "TestPlayer1",
        "email": "testplayer1@example.com",
        "password": "SuperMotDePasse123"
    }

    # Act
    response1 = await client.post("/auth/register", json=player_data)

    # Act — on tente de se connecter avec les mêmes identifiants
    login_data = {
        "username": "TestPlayer1",
        "password": "SuperMotDePasse123"
    }
    response2 = await client.post("/auth/login", data=login_data)
    access_token = response2.json()["access_token"] 
    auth_header = {"Authorization": f"Bearer {access_token}"}
    yield auth_header


@pytest_asyncio.fixture
async def auth_headers_2(client):
    # Arrange
    player_data = {
        "username": "TestPlayer2",
        "email": "testplayer2@example.com",
        "password": "SuperMotDePasse1234"
    }

    # Act
    response1 = await client.post("/auth/register", json=player_data)

    # Act — on tente de se connecter avec les mêmes identifiants
    login_data = {
        "username": "TestPlayer2",
        "password": "SuperMotDePasse1234"
    }
    response2 = await client.post("/auth/login", data=login_data)
    access_token = response2.json()["access_token"] 
    auth_header = {"Authorization": f"Bearer {access_token}"}
    yield auth_header


@pytest_asyncio.fixture
async def match_setup(client, auth_headers, auth_headers_2, db_session):
    # Arrange
    league_data = {
        "name": "Test League",
        "max_teams": 2,
        "max_per_player": 1,
        "total_journeys": 2
    }   

    # Act
    response5 = await client.post("/leagues/", json=league_data, headers=auth_headers)
    response6 = await client.post(f"/leagues/{response5.json()['id']}/join", json={}, headers=auth_headers_2)
    response7 = await client.post(f"/teams/", json={"nom": "Team 1", "nom_stade": "Stadium 1", "id_league": response5.json()['id'], "is_ia": False}, headers=auth_headers)
    response8 = await client.post(f"/teams/", json={"nom": "Team 2", "nom_stade": "Stadium 2", "id_league": response5.json()['id'], "is_ia": False}, headers=auth_headers_2)
    response9 = await client.post(f"/leagues/{response5.json()['id']}/validate", json={}, headers=auth_headers)
    response10 = await client.get(f"/leagues/{response5.json()['id']}/calendar", headers=auth_headers)

    calendar = response10.json()
    yield {
        "league_id": response5.json()['id'],
        "team1_id": response7.json()['id'],
        "team2_id": response8.json()['id'],
        "match_id1": calendar[0]['id'],
        "match_id2": calendar[1]['id'],
    }


@pytest_asyncio.fixture
async def ws_client(client):
    yield ws_test_client