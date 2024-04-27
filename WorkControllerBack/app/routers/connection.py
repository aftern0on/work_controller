import logging
from enum import Enum
from typing import List

from fastapi import APIRouter, WebSocketDisconnect
from starlette.websockets import WebSocket

from app.models import User
from app.schemas import SessionCreate, Session as SessionBase
from app.services.db import UserService
from app.services.websocket import WebSockerManager

websocket_manager = WebSockerManager()
router = APIRouter()


@router.get("/active_session", response_model=List[SessionBase])
async def get_active():
    """Получение всех активных подключений в виде сессий"""

    return websocket_manager.active_connections.keys()


@router.post("/command_to_session/{session_id}/{command}")
async def send_command(session_id: int, command: str):
    """Отправить сообщение активному веб-сокету"""

    for session, websocket in websocket_manager.active_connections.items():
        if session.id == session_id:
            await websocket_manager.send_personal_message(command, websocket)
            return {"error": None}
    return {"error": f"session {session_id} not found"}


@router.websocket("/ws")
async def connect(websocket: WebSocket, username: str, domain: str, machine: str):
    """Подключение и обработка сообщений от веб-сокета, принадлежащего клиенту"""

    # Получение пользователя, создание сессии
    user: User = await UserService.get_by_username(username)
    if not user:
        await websocket_manager.send_personal_message("user not found", websocket)
        raise WebSocketDisconnect
    session_dto: SessionCreate = SessionCreate(
        user=user,
        user_id=user.id,
        domain=domain,
        machine=machine,
        ip_address=websocket.client.host)

    # Проверка на присутствие всех необходимых данных
    if None in (domain, machine):
        await websocket_manager.send_personal_message(f"domain or machine is none", websocket)
        raise WebSocketDisconnect

    session = await websocket_manager.connect(websocket, session_dto)
    logging.info(f"[Websocket] User {username} connected")

    # Обработка сообщений от клиента
    try:
        while True:
            data = await websocket.receive_text()
            if data:
                logging.info(f"[Websocket] User {username} send: {data}")
                if data == "get_screenshot":
                    await websocket_manager.send_personal_message("make screenshot", websocket)
                if data == "remove_connect":
                    await websocket_manager.send_personal_message("disconnect", websocket)
                    raise WebSocketDisconnect
    except WebSocketDisconnect:
        await websocket_manager.disconnect(websocket, session)
