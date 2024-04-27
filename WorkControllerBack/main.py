import logging

from fastapi import FastAPI

from app.database import engine
from app.models import Base
from app.routers import user, session, connection, screenshot


async def create_tables():
    """Создание таблиц, если отсутствуют"""

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

logging.basicConfig(level=logging.INFO)
app = FastAPI()
app.include_router(user.router)
app.include_router(session.router)
app.include_router(connection.router)
app.include_router(screenshot.router)


@app.on_event("startup")
async def startup_event():
    await create_tables()
