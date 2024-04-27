import asyncio
import websockets


async def test_websocket():
    uri = "ws://localhost:8000/ws/1"  # Адаптируйте URI под вашу конфигурацию
    async with websockets.connect(uri) as websocket:
        # Отправка сообщения серверу
        await websocket.send("Hello server!")

        # Получение и печать ответа от сервера
        response = await websocket.recv()  # Используйте recv(), а не receive()
        print(f"Received from server: {response}")

        # Пример отправки команды на запрос скриншота
        await websocket.send("get_screenshot")
        screenshot_response = await websocket.recv()  # Используйте recv()
        print(f"Received screenshot data: {screenshot_response}")

# Запуск асинхронной функции
asyncio.run(test_websocket())
