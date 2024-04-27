# Используем официальный базовый образ Python
FROM python:3.11.2-slim

# Устанавливаем рабочий каталог
WORKDIR /app

# Копируем только файлы Pipenv
COPY Pipfile Pipfile.lock /app/

# Устанавливаем Pipenv и зависимости проекта
RUN pip install pipenv && pipenv install --deploy --ignore-pipfile

# Копируем остальные файлы проекта
COPY . /app

# Устанавливаем переменную окружения, которая сообщает Python не генерировать .pyc
ENV PYTHONDONTWRITEBYTECODE 1

# Устанавливаем переменную окружения, которая сообщает Python не буферизировать stdout и stderr
ENV PYTHONUNBUFFERED 1

# Команда для запуска приложения
CMD ["pipenv", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]