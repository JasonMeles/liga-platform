from fastapi import APIRouter, WebSocket, WebSocketDisconnect
from app.services.connection_manager import manager

router = APIRouter(prefix="/ws", tags=["websockets"])

@router.websocket("/league/{league_id}")
async def websocket_endpoint(websocket: WebSocket, league_id: int):
    await manager.connect(league_id, websocket)
    try:
        while True:
            data = await websocket.receive_text()
            # Traitez les données reçues et éventuellement envoyez une réponse
            await manager.broadcast(league_id, f"Message reçu pour la ligue {league_id}: {data}")
    except WebSocketDisconnect:
        await manager.disconnect(league_id, websocket)
        print(f"WebSocket déconnecté pour la ligue {league_id}")