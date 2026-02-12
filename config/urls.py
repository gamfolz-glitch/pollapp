"""
Основной URL-конфиг проекта
"""

from django.contrib import admin
from django.conf import settings
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),

    # Auth (login, logout, password reset и т.д.)
    path("accounts/", include("django.contrib.auth.urls")),

    # Основное приложение
    path("", include("polls.urls")),
]

# Только в режиме разработки
if settings.DEBUG:
    urlpatterns += [
        path("__reload__/", include("django_browser_reload.urls")),
    ]