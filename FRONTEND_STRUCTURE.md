# Структура фронтенда

## Статические файлы

### CSS
- `static/css/custom.css` - Кастомные стили, анимации и утилиты
  - CSS переменные для цветов
  - Анимации (slideIn, fadeIn, scaleIn, shimmer)
  - Компоненты (card-hover, btn-gradient, input-focus)
  - Утилиты (line-clamp, gradient-text)

### JavaScript
- `static/js/main.js` - Основной JavaScript
  - Инициализация форм с кодом опроса
  - Автофокус полей
  - Подтверждения удаления
  - Утилиты (showNotification, copyToClipboard)

- `static/js/charts.js` - Работа с диаграммами Chart.js
  - Инициализация диаграмм
  - Нормализация процентов
  - Применение цветов к деталям

- `static/js/poll-timer.js` - Таймер опросов
  - Обратный отсчет времени
  - Блокировка формы при истечении времени

## Шаблоны

### Базовые
- `polls/templates/base.html` - Базовый шаблон
  - Мета-теги для SEO
  - Подключение Tailwind CSS (CDN)
  - Подключение Font Awesome
  - Подключение кастомных стилей и скриптов

- `polls/templates/dashboard/base.html` - Базовый шаблон для dashboard

### Публичные страницы
- `polls/templates/polls/index.html` - Главная страница
- `polls/templates/polls/poll_public.html` - Прохождение опроса
- `polls/templates/polls/poll_thanks.html` - Страница благодарности
- `polls/templates/polls/poll_qr.html` - QR-код опроса

### Dashboard
- `polls/templates/polls/project_list.html` - Список опросов
- `polls/templates/dashboard/project_detail.html` - Детали опроса
- `polls/templates/dashboard/project_stats.html` - Статистика
- `polls/templates/dashboard/project_responses.html` - Ответы пользователей
- `polls/templates/dashboard/poll_form.html` - Форма создания/редактирования опроса
- `polls/templates/dashboard/question_form.html` - Форма создания/редактирования вопроса
- `polls/templates/dashboard/choice_form.html` - Форма создания/редактирования варианта
- `polls/templates/dashboard/poll_delete.html` - Подтверждение удаления опроса
- `polls/templates/dashboard/question_delete.html` - Подтверждение удаления вопроса
- `polls/templates/dashboard/choice_delete.html` - Подтверждение удаления варианта

### Аутентификация
- `polls/templates/registration/login.html` - Вход
- `polls/templates/registration/signup.html` - Регистрация

## Внешние зависимости (CDN)

- **Tailwind CSS** - `https://cdn.tailwindcss.com`
- **Font Awesome 6.5.1** - `https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.5.1/css/all.min.css`
- **Chart.js 4.4.0** - `https://cdn.jsdelivr.net/npm/chart.js@4.4.0/dist/chart.umd.min.js`

## Оптимизация для продакшена

1. ✅ Все стили вынесены в отдельные файлы
2. ✅ Все скрипты вынесены в отдельные файлы
3. ✅ Используется WhiteNoise для сжатия статических файлов
4. ✅ Добавлены мета-теги для SEO
5. ✅ Добавлены preconnect и dns-prefetch для быстрой загрузки
6. ✅ Скрипты загружаются с атрибутом `defer`
7. ✅ Добавлены aria-атрибуты для доступности
8. ✅ Все URL используют `{% url %}` теги

## Команды для деплоя

```bash
# Сборка статических файлов
python manage.py collectstatic --noinput

# Проверка перед деплоем
python manage.py check --deploy
```

