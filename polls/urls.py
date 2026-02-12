"""
URL-маршруты для приложения polls.
Разделены на логические группы: публичные, аутентификация, управление, аналитика и API.
"""

from django.urls import path

from .views.public import (
    index,
    poll_code_redirect,
    poll_public,
    poll_thanks,
    poll_qr_page,
    poll_qr_png,
)
from .views.auth import signup
from .views.dashboard import (
    project_list,
    project_new,
    project_detail,
    project_edit,
    project_delete,
)
from .views.questions import (
    question_new,
    question_edit,
    question_delete,
)
from .views.choices import (
    choice_new,
    choice_edit,
    choice_delete,
)
from .views.analytics import (
    project_stats,
    project_responses,
)
from .views.live import live_vote_count

app_name = "polls"

urlpatterns = [
    # PUB: Публичные вьюхи — прохождение опроса
    path("", index, name="index"),
    path("p/", poll_code_redirect, name="poll_code_redirect"),
    path("p/<str:access_code>/", poll_public, name="poll_public"),
    path("p/<str:access_code>/thanks/", poll_thanks, name="poll_thanks"),
    path("p/<str:access_code>/qr/", poll_qr_page, name="poll_qr_page"),
    path("p/<str:access_code>/qr.png/", poll_qr_png, name="poll_qr_png"),

    # AUTH: Аутентификация
    path("accounts/signup/", signup, name="signup"),

    # DASHBOARD: Управление опросами
    path("dashboard/project/", project_list, name="project_list"),
    path("dashboard/project/new/", project_new, name="project_new"),
    path("dashboard/project/<int:poll_id>/", project_detail, name="project_detail"),  # ✅ poll_id
    path("dashboard/project/<int:poll_id>/edit/", project_edit, name="project_edit"),  # ✅ poll_id
    path('poll/<int:pk>/delete/', project_delete, name="project_delete"),  # ✅ poll_id

    # ANALYTICS: Статистика и ответы
    path("dashboard/project/<int:poll_id>/stats/", project_stats, name="project_stats"),  # ✅ poll_id
    path("dashboard/project/<int:poll_id>/responses/", project_responses, name="project_responses"),  # ✅ poll_id

    # QUESTIONS: Управление вопросами
    path("dashboard/project/<int:poll_id>/question/new/", question_new, name="question_new"),  # ✅ poll_id
    path("dashboard/project/<int:poll_id>/question/<int:question_id>/edit/", question_edit, name="question_edit"),
    path("dashboard/project/<int:poll_id>/question/<int:question_id>/delete/", question_delete, name="question_delete"),

    # CHOICES: Управление вариантами
    path("dashboard/project/<int:poll_id>/question/<int:question_id>/choice/new/", choice_new, name="choice_new"),
    path("dashboard/project/<int:poll_id>/question/<int:question_id>/choice/<int:choice_id>/edit/", choice_edit, name="choice_edit"),
    path("dashboard/project/<int:poll_id>/question/<int:question_id>/choice/<int:choice_id>/delete/", choice_delete, name="choice_delete"),

    # PRESENT: Live-статистика (для презентаций)
    path("api/live/vote-count/", live_vote_count, name="live_vote_count"),
]