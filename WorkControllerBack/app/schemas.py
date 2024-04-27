from datetime import datetime
from typing import Optional

from fastapi import UploadFile
from pydantic import BaseModel


class UserBase(BaseModel):
    """ДТО для определения модели пользователя"""

    username: str


class UserCreate(UserBase):
    """ДТО для чтения данных пользователя, может включать другие специфические поля в дальнейшем"""
    pass


class User(UserBase):
    """ДТО для взаимодействия через ORM с данными пользователя"""

    id: int

    class Config:
        from_attributes = True


class SessionBase(BaseModel):
    """ДТО для взаимодействия со сессиями"""

    user_id: int
    start_time: Optional[datetime] = None
    last_active_time: Optional[datetime] = None
    domain: Optional[str] = None
    machine: Optional[str] = None
    ip_address: Optional[str] = None


class SessionCreate(SessionBase):
    """ДТО для создания новой сессии, принадлежащей указанному пользователю"""

    pass


class Session(SessionBase):
    """ДТО для взаимодействия с данными сессий через ORM"""

    id: int

    class Config:
        from_attributes = True


class ScreenshotBase(BaseModel):
    """ДТО для взаимодействия со скриншотами"""

    session_id: int
    create_at: Optional[datetime] = None


class ScreenshotCreate(SessionBase):
    """ДТО для создания скриншотов"""

    image_data: bytes


class ScreenshotGet(ScreenshotBase):
    """ДТО для получения основных данных скриншота без содержания"""

    id: int


class Screenshot(ScreenshotBase):
    """ДТО для взаимодействия со скриншотами через ORM"""

    id: int
    image_data: bytes

    class Config:
        from_attributes = True
