from typing import List

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.services.db import SessionService
from ..schemas import SessionCreate, Session as SessionModel

router = APIRouter()


@router.post("/sessions/", response_model=SessionModel)
async def create_session(session: SessionCreate):
    """Создать новую сессию пользователя"""

    return await SessionService.create(session)


@router.get("/sessions/{user_id}", response_model=List[SessionModel])
async def get_user_sessions(user_id: int):
    """Получить сессии которые принадлежат пользователю с указанным ID"""

    return await SessionService.get_by_user(user_id)
