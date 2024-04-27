from fastapi import UploadFile
from sqlalchemy import select, func
from app.database import get_session
from app.models import Session as DBSession
from app.models import User as DBUser
from app.models import Screenshot as DBScreenshot
from app.schemas import SessionCreate
from app.schemas import UserCreate


class SessionService:
    """Инструменты для работы с таблицей сессий"""

    @staticmethod
    async def create(session: SessionCreate) -> DBSession:
        """Создание сессии"""

        async with get_session() as db:
            new_session = DBSession(**session.dict())
            db.add(new_session)
            await db.commit()
            await db.refresh(new_session)
            return new_session

    @staticmethod
    async def update_end_time(session_id: int):
        async with get_session() as db:
            session = await db.execute(select(DBSession).where(DBSession.id == session_id))
            session = session.scalars().first()
            session.last_active_time = func.now()
            await db.commit()
            await db.refresh(session)

    @staticmethod
    async def get_by_user(user_id: int):
        """Получение всех сессий пользователя"""

        async with get_session() as db:
            result = await db.execute(select(DBSession).where(DBSession.user_id == user_id))
            return result.scalars().all()


class UserService:
    """Инструменты для работы с таблицей пользователей"""

    @staticmethod
    async def create(user: UserCreate):
        """Создание пользователя"""

        async with get_session() as db:
            new_user = DBUser(**user.dict())
            db.add(new_user)
            await db.commit()
            await db.refresh(new_user)
            return new_user

    @staticmethod
    async def get():
        """Получение списка всех пользователей"""

        async with get_session() as db:
            result = await db.execute(select(DBUser))
            return result.scalars().all()

    @staticmethod
    async def get_by_username(username: str):
        """Получение пользователя по его username"""

        async with get_session() as db:
            result = await db.execute(select(DBUser).filter(DBUser.username == username))
            return result.scalars().first()


class ScreenshotService:
    """Инструмент для работы со скриншотами"""

    @staticmethod
    async def create(file, session_id: int):
        """Создание нового скриншота сессии"""

        async with get_session() as db:
            new_screenshot = DBScreenshot(session_id=session_id, image_data=file)
            db.add(new_screenshot)
            await db.commit()
            await db.refresh(new_screenshot)
            return new_screenshot

    @staticmethod
    async def get_by_session(session_id: int):
        """Получение всех скриншотов сессии"""

        async with get_session() as db:
            result = await db.execute(select(DBScreenshot).filter(DBScreenshot.session_id == session_id))
            return result.scalars().all()

    @staticmethod
    async def get(screenshot_id: int):
        """Получение скриншота по его id"""

        async with get_session() as db:
            result = await db.execute(select(DBScreenshot).filter(DBScreenshot.id == screenshot_id))
            return result.scalars().first()
