# Contributing
Спасибо за интерес к проекту.

## Быстрый старт разработки
1. Создайте виртуальное окружение и установите зависимости:
   - Windows (PowerShell):
     - `py -m venv .venv`
     - `.\.venv\Scripts\python -m pip install -r requirements.txt`
2. Примените миграции и запустите сервер:
   - `.\.venv\Scripts\python manage.py migrate`
   - `.\.venv\Scripts\python manage.py runserver`

## Проверки перед PR
- Тесты: `python manage.py test`
- Линтер: `ruff check .`

## Стиль
- Python: Ruff (см. `pyproject.toml`).
- Предпочтение простым и читаемым решениям.

## Pull Requests
- Один PR = одна логическая задача.
- Опишите мотивацию и как проверить изменения.
