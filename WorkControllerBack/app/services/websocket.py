from typing import List, Dict
from fastapi import WebSocket

from app.models import Session
from app.schemas import SessionCreate
from app.services.db import SessionService


class WebSockerManager:
    def __init__(self):
        """Инструмент для работы с подключениями по веб-сокетам"""

        self.active_connections: Dict[Session, WebSocket] = {}

    async def connect(self, websocket: WebSocket, session_dto: SessionCreate) -> Session:
        """Создание подключения по веб-сокету. Вместе с подключением создается сессия"""

        await websocket.accept()
        session = await SessionService.create(session_dto)
        self.active_connections[session] = websocket
        await self.send_personal_message(f"session {session.id}", websocket)
        return session

    async def disconnect(self, websocket: WebSocket, session: Session):
        """Отключение от веб-сокета"""

        del self.active_connections[session]
        await SessionService.update_end_time(session.id)
        try:
            await websocket.close()
        except RuntimeError:
            pass

    @staticmethod
    async def send_personal_message(message: str, websocket: WebSocket):
        """Отправление команды веб-сокету"""

        await websocket.send_text(message)

    async def broadcast(self, message: str):
        """Отправить сообщение всем подключениям"""

        for connection in self.active_connections.values():
            await connection.send_text(message)
