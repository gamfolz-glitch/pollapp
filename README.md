# Система опросов (Django)
Учебный проект: полноценное веб‑приложение для создания опросов, сбора ответов и просмотра статистики.

Проект задуман так, чтобы его было удобно:
- запускать локально (как учебный пример Django)
- деплоить в продакшн (gunicorn + переменные окружения + Docker)

## Возможности
### Для создателя опросов (dashboard)
- регистрация / вход
- создание опросов
- добавление вопросов трёх типов:
  - TEXT — текстовый ответ
  - SINGLE — один вариант
  - MULTI — несколько вариантов
- CRUD вопросов и вариантов ответов
- просмотр:
  - страницы статистики
  - таблицы всех отправок (по строке на отправку)
- QR‑код (страница для печати + PNG)

### Для участников
- вход по короткому коду опроса
- прохождение опроса по URL вида `/p/<CODE>/`
- сохранение отправок (Submission) и ответов (Answer/AnswerChoice)

## Технологии
- Django 5.x
- SQLite по умолчанию (для простоты)
- опционально: Postgres через `DATABASE_URL`
- WhiteNoise для раздачи статических файлов в production
- Gunicorn как production WSGI-сервер

## Архитектура (как устроено)
### Основные модели
- `Poll`: опрос (title/description/owner/access_code)
- `Question`: вопрос (poll/text/kind/order)
- `Choice`: вариант ответа для SINGLE/MULTI
- `Submission`: одна «отправка» (poll/user/created_at)
- `Answer`: ответ на вопрос (submission/question/text_value)
- `AnswerChoice`: связь Answer ↔ Choice для MULTI/SINGLE

### Основные маршруты
- `/` — главная страница + ввод кода опроса
- `/accounts/*` — стандартные auth-страницы Django + signup
- `/dashboard/project/` — список опросов пользователя
- `/dashboard/project/<poll_id>/` — управление конкретным опросом
- `/dashboard/project/<poll_id>/stats/` — статистика
- `/dashboard/project/<poll_id>/responses/` — ответы (таблица)
- `/p/<access_code>/` — публичный опрос
- `/p/<access_code>/qr/` и `/p/<access_code>/qr.png` — QR
- `/present/live_vote_count?code=<access_code>` — JSON агрегаты (для «лайв» отображения)

## Быстрый старт (Windows / PowerShell)
```pwsh
py -m venv .venv
.\.venv\Scripts\python -m pip install --upgrade pip
.\.venv\Scripts\python -m pip install -r requirements.txt

# (опционально) локальные переменные окружения
Copy-Item .env.example .env

.\.venv\Scripts\python manage.py migrate
.\.venv\Scripts\python manage.py createsuperuser
.\.venv\Scripts\python manage.py runserver
```

## Быстрый старт (Linux/macOS)
```bash
python3 -m venv .venv
./.venv/bin/python -m pip install --upgrade pip
./.venv/bin/python -m pip install -r requirements.txt

cp .env.example .env

./.venv/bin/python manage.py migrate
./.venv/bin/python manage.py createsuperuser
./.venv/bin/python manage.py runserver
```

## Переменные окружения
Проект читает настройки из переменных окружения (и из `.env`, если он есть).

Основные:
- `DJANGO_DEBUG` — `1` (dev) или `0` (production)
- `DJANGO_SECRET_KEY` — секретный ключ Django (обязательно в production)
- `DJANGO_ALLOWED_HOSTS` — список хостов через запятую
- `DJANGO_CSRF_TRUSTED_ORIGINS` — список origin’ов (с `https://`) через запятую

База данных:
- `DATABASE_URL` — если задан, используется вместо SQLite

Production HTTPS:
- `DJANGO_SECURE_SSL_REDIRECT` — редирект на https
- `DJANGO_SESSION_COOKIE_SECURE`, `DJANGO_CSRF_COOKIE_SECURE`
- HSTS: `DJANGO_SECURE_HSTS_SECONDS` и связанные флаги (по умолчанию 0)

См. `.env.example`.

## Тесты
```bash
python manage.py test
```

## Линтер
```bash
ruff check .
```

## Docker (production-like)
1) Создайте `.env`:
- `cp .env.example .env`
- обязательно задайте `DJANGO_SECRET_KEY` и `DJANGO_DEBUG=0`

2) Запуск:
```bash
docker compose up --build
```
Откройте `http://localhost:8000`.

## Production запуск без Docker (пример)
1) Настройте env (`DJANGO_DEBUG=0`, `DJANGO_SECRET_KEY`, `DJANGO_ALLOWED_HOSTS` и т.д.)
2) Примените миграции и соберите статику:
```bash
python manage.py migrate
python manage.py collectstatic --noinput
```
3) Запустите gunicorn:
```bash
gunicorn config.wsgi:application --bind 0.0.0.0:8000
```

## Структура репозитория
- `config/` — Django project (settings/urls/wsgi/asgi)
- `polls/` — Django app
- `static/` — проектные статические файлы (пока пусто, заготовка)
- `docker/` — entrypoint для контейнера

## Лицензия
MIT (см. `LICENSE`).
