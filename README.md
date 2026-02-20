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

