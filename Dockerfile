FROM python:3.11-slim

WORKDIR /app

# Копируем только зависимости на раннем этапе
COPY requirements.txt .

# Установка зависимостей
RUN pip install --upgrade pip \
    && pip install --no-cache-dir -r requirements.txt

# Копируем остальное
COPY . .

# Убираем локальное виртуальное окружение
RUN rm -rf .venv venv

ENV PYTHONUNBUFFERED=1

CMD ["python", "main.py"]