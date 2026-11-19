"""Content negotiation: CSV-рендерер, 415 і кастомний заголовок табло."""


def test_scoreboard_default_is_json(api):
    response = api.get("/api/v1/scoreboard/")
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("application/json")
    assert isinstance(response.json(), list)


def test_scoreboard_csv_via_format_param(api):
    response = api.get("/api/v1/scoreboard/?format=csv")
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("text/csv"), (
        "?format=csv вибирає рендерер за його атрибутом format."
    )
    first_line = response.text.splitlines()[0]
    assert first_line.startswith("home_name,away_name"), (
        "Перший рядок CSV — шапка з назвами колонок."
    )


def test_scoreboard_csv_via_accept_header(api):
    response = api.get("/api/v1/scoreboard/", headers={"Accept": "text/csv"})
    assert response.status_code == 200
    assert response.headers["Content-Type"].startswith("text/csv"), (
        "Той самий рендерер вибирається заголовком Accept — це і є "
        "content negotiation: Accept питає формат, Content-Type його оголошує."
    )


def test_csv_has_one_row_per_live_match(api):
    rows = api.get("/api/v1/scoreboard/?format=csv").text.strip().splitlines()
    live = api.get("/api/v1/scoreboard/").json()
    assert len(rows) == len(live) + 1, "Рядків даних стільки ж, скільки матчів, плюс шапка."


def test_unacceptable_accept_gives_406(api):
    response = api.get("/api/v1/scoreboard/", headers={"Accept": "application/xml"})
    assert response.status_code == 406, (
        "Клієнт просить формат, якого сервер не вміє віддавати — це 406 "
        "Not Acceptable, і відповідає за нього Accept, а не Content-Type."
    )


def test_unsupported_content_type_gives_415(api, tournament, team_ids):
    response = api.post(
        "/api/v1/matches/",
        data=b"<match></match>",
        headers={"Content-Type": "application/xml"},
    )
    assert response.status_code == 415, (
        "415 означає «не вмію читати цей формат тіла» — і до валідації "
        "справа навіть не доходить, тому це не 400."
    )


def test_scoreboard_sends_poll_after(api):
    """Табло підказує клієнтові період опитування власним заголовком.

    Навіщо взагалі заголовок, а не поле в тілі: це вказівка **клієнтові**,
    як користуватись цим API, а не частина даних про матчі. Тіло — це
    відповідь на питання «який рахунок», заголовок — на питання «коли
    питати знову».

    Чому саме кастомний: стандартного заголовка з таким змістом немає
    (`Retry-After` зарезервований за `503` і `429`), тому його вигадує
    автор API — і саме тому браузер із іншого origin за замовчуванням
    ховає його від JS.
    """
    response = api.get("/api/v1/scoreboard/")
    assert "X-Poll-After" in response.headers, (
        "Табло має сказати клієнтові, через скільки секунд опитувати його "
        "знову — саме цей заголовок потім доведеться відкривати через "
        "CORS_EXPOSE_HEADERS."
    )
    value = int(response.headers["X-Poll-After"])
    assert 5 <= value <= 300, (
        "Нижня межа захищає сервер від опитування щосекунди, верхня не дає "
        f"табло застигнути. Отримано {value}."
    )


def test_poll_after_is_short_while_a_match_is_live(api, live_seeded_match):
    """Поки матч триває — опитувати часто."""
    response = api.get("/api/v1/scoreboard/")
    assert response.json(), "у табло має бути хоча б один живий матч"
    assert int(response.headers["X-Poll-After"]) == 5, (
        "Поки є живий матч, рахунок може змінитись будь-якої миті, тому "
        "сервер просить опитувати з мінімальним періодом."
    )


def test_poll_after_is_not_derivable_from_the_body(api):
    """Головна причина, чому це заголовок, а не поле у відповіді.

    Клієнт не може обчислити це число сам: у тілі табло лише матчі, що
    **тривають**, а період спирається на час початку найближчого
    **запланованого** — його в тілі немає взагалі. Тому заголовок несе
    інформацію, якої у відповіді більше ніде немає.
    """
    response = api.get("/api/v1/scoreboard/")
    body = response.json()
    value = int(response.headers["X-Poll-After"])
    if not body:
        assert value > 5, (
            "Живих матчів немає, тож опитувати щоп'ять секунд нема сенсу: "
            "сервер мав порахувати час до найближчого запланованого матчу "
            "або віддати стелю."
        )
    for match in body:
        assert "poll_after" not in match and "X-Poll-After" not in match, (
            "Це вказівка клієнтові, а не поле ресурсу — у тілі його бути не має."
        )
