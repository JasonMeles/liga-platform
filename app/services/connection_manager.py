from fastapi import WebSocket

class ConnectionManager:
    def __init__(self):
        # notre dictionnaire { id_ligue: [ws1, ws2] }
        self.league_connections = {}

    async def connect(self, league_id: int, websocket: WebSocket):
        # 1. accepter la connexion
        await websocket.accept()
        # 2. ajouter le websocket à la bonne liste
        if league_id not in self.league_connections:
            self.league_connections[league_id] = []
        if websocket not in self.league_connections[league_id]:
            self.league_connections[league_id].append(websocket)
    
    def disconnect(self, league_id: int, websocket: WebSocket):
        # 1. retirer le websocket de la bonne liste
        if league_id in self.league_connections and websocket in self.league_connections[league_id]:
            self.league_connections[league_id].remove(websocket)
    
    async def broadcast(self, league_id: int, message: str):
        # 1. envoyer le message à tous les websockets de la bonne liste
        if league_id in self.league_connections:
            for connection in self.league_connections[league_id]:
                await connection.send_text(message)
                
# Singleton pour le ConnectionManager
manager = ConnectionManager()