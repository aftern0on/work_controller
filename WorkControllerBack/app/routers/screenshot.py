import io
from typing import List

from fastapi import APIRouter, UploadFile, File
from fastapi.responses import StreamingResponse

from app.schemas import Screenshot, ScreenshotGet
from app.services.db import ScreenshotService

router = APIRouter()


@router.post("/screenshot/{session_id}", response_model=ScreenshotGet)
async def send_screenshot(file: UploadFile, session_id: int):
    """Получение скриншота рабочего стола"""

    content = await file.read()
    return await ScreenshotService.create(content, session_id)


@router.get("/screenshots/{session_id}", response_model=List[ScreenshotGet])
async def get_screenshots(session_id: int):
    """Получение списка всех скриншотов сессии"""

    screenshots = await ScreenshotService.get_by_session(session_id=session_id)
    return screenshots


@router.get("/screenshot/{screenshot_id}")
async def get_screenshot(screenshot_id: int):
    """Получение конкретного скриншота по его id"""

    screenshot = await ScreenshotService.get(screenshot_id)
    return StreamingResponse(io.BytesIO(screenshot.image_data), media_type='image/png')
