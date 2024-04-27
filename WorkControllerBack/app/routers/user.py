from typing import List
from fastapi import APIRouter, HTTPException

from ..schemas import UserCreate, User as UserSchema
from ..services.db import UserService

router = APIRouter()


@router.post("/user", response_model=UserSchema)
async def create(user: UserCreate):
    """Эндпроинт для создания записи пользователя в БД"""

    return await UserService.create(user)


@router.get("/user/{username}", response_model=UserSchema)
async def get_by_username(username: str):
    """Получение пользователя по username"""

    user = await UserService.get_by_username(username)
    if not user:
        raise HTTPException(status_code=404, detail=f"User {username} not found")
    return user


@router.get('/users', response_model=List[UserSchema])
async def get_list():
    """Эндпоинт для чтения записей пользователей в БД"""

    return await UserService.get()
