"""
URL-маршруты для приложения polls.
Разделены на логические группы.
"""

from django.urls import path

from . import views

app_name = "polls"

urlpatterns = [
    # PUB: Публичные вьюхи — прохождение опроса
    path("", views.index, name="index"),
    path("p/", views.poll_code_redirect, name="poll_code_redirect"),
    path("p/<str:access_code>/", views.poll_public, name="poll_public"),
    path("p/<str:access_code>", views.poll_public),
    path("p/<str:access_code>/thanks/", views.poll_thanks, name="poll_thanks"),
    path("p/<str:access_code>/thanks", views.poll_thanks),
    path("p/<str:access_code>/qr/", views.poll_qr_page, name="poll_qr_page"),
    path("p/<str:access_code>/qr", views.poll_qr_page),
    path("p/<str:access_code>/qr.png", views.poll_qr_png, name="poll_qr_png"),

    # AUTH: Аутентификация
    path("accounts/signup/", views.signup, name="signup"),

    # DASHBOARD: Управление опросами (для владельца)
    path("dashboard/project/", views.project_list, name="project_list"),
    path("dashboard/project/new/", views.project_new, name="project_new"),
    path("dashboard/project/<int:poll_id>/", views.project_detail, name="project_detail"),
    path("dashboard/project/<int:poll_id>/edit/", views.project_edit, name="project_edit"),
    path("dashboard/project/<int:poll_id>/delete/", views.project_delete, name="project_delete"),
    path("dashboard/project/<int:poll_id>/stats/", views.project_stats, name="project_stats"),
    path("dashboard/project/<int:poll_id>/responses/", views.project_responses, name="project_responses"),

    # QUESTIONS: Управление вопросами
    path("dashboard/project/<int:poll_id>/question/new/", views.question_new, name="question_new"),
    path("dashboard/project/<int:poll_id>/question/<int:question_id>/edit/", views.question_edit, name="question_edit"),
    path("dashboard/project/<int:poll_id>/question/<int:question_id>/delete/", views.question_delete, name="question_delete"),

    # CHOICES: Управление вариантами
    path("dashboard/project/<int:poll_id>/question/<int:question_id>/choice/new/", views.choice_new, name="choice_new"),
    path("dashboard/project/<int:poll_id>/question/<int:question_id>/choice/<int:choice_id>/edit/", views.choice_edit, name="choice_edit"),
    path("dashboard/project/<int:poll_id>/question/<int:question_id>/choice/<int:choice_id>/delete/", views.choice_delete, name="choice_delete"),

    # PRESENT: Live-статистика (для презентаций)
    path("present/live_vote_count/", views.live_vote_count, name="live_vote_count"),
    path("present/live_vote_count", views.live_vote_count),
    path( "api/question/<int:question_id>/correct-count/",
    views.question_correct_count,
    name="question_correct_count"
),
]