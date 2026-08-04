import pytest


@pytest.mark.asyncio
async def test_register_player(client):
    # Arrange
    player_data = {
        "username": "TestPlayer1",
        "email": "testplayer1@example.com",
        "password": "SuperMotDePasse123"
    }

    # Act
    response = await client.post("/auth/register", json=player_data)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "bearer"


@pytest.mark.asyncio
async def test_register_duplicate_username(client):
    # Arrange
    player_data = {
        "username": "TestPlayer1",
        "email": "testplayer1@example.com",
        "password": "SuperMotDePasse123"
    }

    # Act — premier enregistrement
    first_response = await client.post("/auth/register", json=player_data)

    # Act — deuxième enregistrement avec le même username (email différent)
    duplicate_data = {
        "username": "TestPlayer1",
        "email": "autre_email@example.com",
        "password": "AutreMotDePasse456"
    }
    second_response = await client.post("/auth/register", json=duplicate_data)

    # Assert
    assert first_response.status_code == 200
    assert second_response.status_code == 400

@pytest.mark.asyncio
async def test_login_success(client):
    # Arrange — on crée d'abord un joueur via register
    register_data = {
        "username": "LoginTestPlayer",
        "email": "logintest@example.com",
        "password": "MonMotDePasse789"
    }
    await client.post("/auth/register", json=register_data)

    # Act — on tente de se connecter avec les mêmes identifiants
    login_data = {
        "username": "LoginTestPlayer",
        "password": "MonMotDePasse789"
    }
    response = await client.post("/auth/login", data=login_data)

    # Assert
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_wrong_password(client):
    # Arrange — on crée un joueur avec un mot de passe connu
    register_data = {
        "username": "WrongPassPlayer",
        "email": "wrongpass@example.com",
        "password": "BonMotDePasse123"
    }
    await client.post("/auth/register", json=register_data)

    # Act — on tente de se connecter avec le MAUVAIS mot de passe
    login_data = {
        "username": "WrongPassPlayer",
        "password": "MauvaisMotDePasse999"
    }
    response = await client.post("/auth/login", data=login_data)

    # Assert
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_login_nonexistent_username(client):
    # Act — on tente de se connecter avec un username qui n'a jamais été enregistré
    login_data = {
        "username": "UsernameQuiNexistePas",
        "password": "PeuImporteLeMotDePasse"
    }
    response = await client.post("/auth/login", data=login_data)

    # Assert
    assert response.status_code == 401

