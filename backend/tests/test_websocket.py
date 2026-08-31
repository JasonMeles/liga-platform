import pytest
from sqlalchemy import select
import concurrent.futures

def test_websocket_broadcast_basic(ws_client, match_setup):
    with ws_client.websocket_connect(f"/ws/league/{match_setup['league_id']}") as websocket:
        websocket.send_text("Bonjour")
        data = websocket.receive_text()
        assert "Bonjour" in data

@pytest.mark.asyncio
async def test_websocket_isolation_between_leagues(ws_client, match_setup, auth_headers, client):
    # Create a second league and connect to it
    league_data = {
        "name": "Test League 2",
        "max_teams": 2,
        "max_per_player": 1,
        "total_journeys": 2
    }
    response = await client.post("/leagues/", json=league_data, headers=auth_headers)
    league_id_2 = response.json()['id']

    with ws_client.websocket_connect(f"/ws/league/{match_setup['league_id']}") as websocket1, ws_client.websocket_connect(f"/ws/league/{league_id_2}") as websocket2:
        websocket1.send_text("Message pour la ligue 1")
        data1 = websocket1.receive_text()
        assert "Message pour la ligue 1" in data1
        executor =  concurrent.futures.ThreadPoolExecutor()
        future = executor.submit(websocket2.receive_text)
        try:
            future.result(timeout=1)
            pytest.fail("Le client 2 n'aurait pas dû recevoir de message")
        except concurrent.futures.TimeoutError:
            pass  # Comportement attendu : rien reçu dans le délai
        finally:
                executor.shutdown(wait=False)

def test_websocket_broadcast_to_all_clients(ws_client, match_setup):
    with ws_client.websocket_connect(f"/ws/league/{match_setup['league_id']}") as websocket1, ws_client.websocket_connect(f"/ws/league/{match_setup['league_id']}") as websocket2:
        websocket1.send_text("Message pour tous les clients")
        data1 = websocket1.receive_text()
        data2 = websocket2.receive_text()
        assert "Message pour tous les clients" in data1
        assert "Message pour tous les clients" in data2
