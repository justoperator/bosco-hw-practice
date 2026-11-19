"""Пагінація з керованим розміром сторінки."""

PAGINATION_KEYS = {"count", "next", "previous", "results"}


def test_envelope_is_unchanged(api):
    """Регресія: конверт із ПР №2.16.3 має лишитись той самий."""
    body = api.get("/api/v1/matches/").json()
    assert set(body) == PAGINATION_KEYS


def test_page_size_is_respected(api):
    body = api.get("/api/v1/matches/?page_size=1").json()
    assert len(body["results"]) == 1, (
        "?page_size=1 має віддати один елемент: потрібен page_size_query_param."
    )
    assert body["count"] > 1, "У базі більше одного матчу — count це загальна кількість."


def test_page_size_is_capped(api):
    body = api.get("/api/v1/matches/?page_size=100000").json()
    assert len(body["results"]) <= 50, (
        "Без max_page_size один запит віддає всю таблицю, і пагінація "
        "перестає захищати сервер."
    )


def test_second_page_has_previous(api):
    body = api.get("/api/v1/matches/?page_size=1&page=2").json()
    assert body["previous"] is not None
    assert body["results"]


def test_page_out_of_range_gives_404(api):
    response = api.get("/api/v1/matches/?page=99999")
    assert response.status_code == 404, (
        "Неіснуюча сторінка — 404 від пагінатора, а не порожній список."
    )
