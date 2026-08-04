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

load_dotenv()

TEST_DATABASE_URL = os.getenv("TEST_DATABASE_URL")


test_engine = create_async_engine(TEST_DATABASE_URL, echo=False, poolclass=NullPool)
TestSessionLocal = sessionmaker(
    test_engine,
    class_=AsyncSession,
    expire_on_commit=False
)


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
async def client(db_session):
    # On remplace get_db par une version qui utilise la session de test
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
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

