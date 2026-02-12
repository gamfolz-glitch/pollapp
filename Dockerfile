# === Stage 1: Build with dev dependencies ===
FROM python:3.12-slim AS builder

WORKDIR /app

# Установка системных зависимостей (для компиляции psycopg, PIL и др.)
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        build-essential \
        libpq-dev \
        libjpeg-dev \
        libpng-dev \
        libwebp-dev \
        zlib1g-dev \
        git \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Копируем только requirements сначала (кеширование)
COPY requirements.txt .

# Установка всех зависимостей (включая dev для tailwind)
RUN pip install --no-cache-dir -r requirements.txt

# Копируем код
COPY . .

# Собираем статику: tailwind + collectstatic
RUN python manage.py tailwind build
RUN python manage.py collectstatic --noinput


# === Stage 2: Final production image ===
FROM python:3.12-slim AS production

WORKDIR /app

# Установка только продакшен-зависимостей
COPY requirements.txt .
RUN pip install --no-cache-dir --no-dev -r requirements.txt && \
    # Удаляем ненужные пакеты (если они не нужны в runtime)
    pip uninstall -y django-tailwind django-browser-reload ruff || true

# Копируем собранные статические файлы из builder
COPY --from=builder /app/staticfiles /app/staticfiles

# Копируем только нужные исходники
COPY config/ config/
COPY polls/ polls/
COPY manage.py .

# Создаем пользователя безопасности
RUN adduser --disabled-password --gecos '' appuser && \
    chown -R appuser:appuser /app
USER appuser

# Порт
EXPOSE 8000

# Команда запуска
CMD ["sh", "-c", "python manage.py migrate --noinput && gunicorn config.wsgi:application --bind 0.0.0.0:8000"]