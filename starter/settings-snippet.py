"""Що додати у settings.py перед початком ПР №2.17.3.

Усе, що було в ПР №2.16.3, лишається. Нового — три пакети і дві
CORS-змінні. Пагінація більше не налаштовується глобальним числом:
розмір сторінки стає керованим, тому клас пагінації живе у вашому коді.
"""

INSTALLED_APPS = [
    # ...
    "rest_framework",
    "django_filters",   # ← нове
    "corsheaders",      # ← нове
    "scoreboard",
]

MIDDLEWARE = [
    # CorsMiddleware мусить стояти ВИЩЕ за CommonMiddleware — інакше
    # редірект CommonMiddleware піде без CORS-заголовків, і браузер
    # приховає відповідь, хоча сервер відпрацював правильно.
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    # ...
]

REST_FRAMEWORK = {
    # Залишається з ПР №2.16.3: конверт {count, next, previous, results}.
    # Власний клас із page_size_query_param підключається у в'юсі.
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 20,
}

# Рівно один дозволений origin. Зірочки тут бути не повинно: з
# CORS_ALLOW_ALL_ORIGINS = True перевірка «чужий origin не проходить"
# стає неперевірюваною.
CORS_ALLOWED_ORIGINS = ["http://localhost:3000"]

# Без цього рядка заголовок у відповіді є, а JS бачить undefined.
CORS_EXPOSE_HEADERS = ["X-Poll-After"]

USE_TZ = True
TIME_ZONE = "Europe/Kyiv"
