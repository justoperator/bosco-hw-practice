"""CORS: що саме сервер обіцяє браузерові.

Ці перевірки — не емуляція браузера. Браузер нічого не питає в сервера про
дозволи: він надсилає звичайний запит, а потім **сам** приховує відповідь,
якщо заголовків немає. Тести дивляться рівно на ці заголовки.
"""

ALLOWED = "http://localhost:3000"
FOREIGN = "http://evil.example"


def test_allowed_origin_gets_allow_origin_header(api):
    response = api.get("/api/v1/matches/", headers={"Origin": ALLOWED})
    assert response.status_code == 200
    assert response.headers.get("Access-Control-Allow-Origin") == ALLOWED, (
        "Для дозволеного origin сервер віддає його ж у Access-Control-Allow-Origin."
    )


def test_foreign_origin_gets_no_allow_origin_header(api):
    response = api.get("/api/v1/matches/", headers={"Origin": FOREIGN})
    assert response.status_code == 200, (
        "Найважливіше у CORS: запит **дійшов і виконався**. Сервер відповів 200, "
        "і лише браузер приховає цю відповідь від JS."
    )
    assert "Access-Control-Allow-Origin" not in response.headers, (
        "Чужому origin заголовок не видається — інакше CORS_ALLOWED_ORIGINS "
        "нічого не обмежує (перевірте, що немає CORS_ALLOW_ALL_ORIGINS=True)."
    )


def test_preflight_for_json_post_is_answered(api):
    response = api.session.options(
        api.url("/api/v1/matches/"),
        headers={
            "Origin": ALLOWED,
            "Access-Control-Request-Method": "POST",
            "Access-Control-Request-Headers": "content-type",
        },
        timeout=5,
    )
    assert response.status_code in (200, 204), (
        "Preflight OPTIONS має отримати відповідь від CorsMiddleware. "
        "Якщо тут 401 або 403 — перевірте порядок middleware: CorsMiddleware "
        "мусить стояти вище за все, що вимагає автентифікації."
    )
    assert response.headers.get("Access-Control-Allow-Origin") == ALLOWED
    assert "POST" in response.headers.get("Access-Control-Allow-Methods", "")


def test_preflight_allows_authorization_header(api):
    """Анонс II семестру: з токеном preflight буде на **кожному** запиті."""
    response = api.session.options(
        api.url("/api/v1/matches/"),
        headers={
            "Origin": ALLOWED,
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "authorization",
        },
        timeout=5,
    )
    assert response.status_code in (200, 204)
    allowed = response.headers.get("Access-Control-Allow-Headers", "").lower()
    assert "authorization" in allowed, (
        "Заголовок Authorization робить запит непростим, тому браузер спершу "
        "запитає дозвіл саме на нього."
    )


def test_poll_after_is_exposed(api):
    response = api.get("/api/v1/scoreboard/", headers={"Origin": ALLOWED})
    exposed = response.headers.get("Access-Control-Expose-Headers", "")
    assert "X-Poll-After" in exposed, (
        "Кастомний заголовок приходить у відповіді, але JS його не побачить, "
        "поки він не перелічений у CORS_EXPOSE_HEADERS. Це найменш відома "
        "частина CORS і найчастіша причина «заголовок є, а undefined»."
    )
