"""Фільтри, пошук і сортування списку матчів."""

from conftest import items


def test_filter_by_status(api, live_seeded_match):
    response = api.get("/api/v1/matches/?status=live")
    assert response.status_code == 200
    results = items(response.json())
    assert results, "У сиді є матч, що триває, — фільтр не має віддавати порожньо."
    assert all(m["status"] == "live" for m in results), (
        "У відповідь потрапили матчі в інших станах: фільтр не застосувався."
    )


def test_filter_by_tournament(api, tournament):
    response = api.get(f"/api/v1/matches/?tournament={tournament['id']}")
    assert response.status_code == 200
    results = items(response.json())
    assert results
    assert all(m["tournament"] == tournament["id"] for m in results)


def test_filter_by_team_covers_home_and_away(api, live_seeded_match):
    team_id = live_seeded_match["away"]
    response = api.get(f"/api/v1/matches/?team={team_id}")
    assert response.status_code == 200
    results = items(response.json())
    assert any(m["id"] == live_seeded_match["id"] for m in results), (
        "Матч, у якому команда грає в гостях, має потрапити у вибірку: "
        "фільтр по команді — це OR по home і away, а не фільтр по home."
    )
    assert all(team_id in (m["home"], m["away"]) for m in results)


def test_unknown_status_value_gives_400(api):
    response = api.get("/api/v1/matches/?status=bogus")
    assert response.status_code == 400, (
        "Невідоме значення фільтра — це 400, а не тихий порожній список. "
        "Такий фільтр має бути оголошений ChoiceFilter зі списком станів."
    )
    assert "status" in response.json()


def test_search_by_team_name(api, live_seeded_match):
    fragment = live_seeded_match["home_name"][:4]
    response = api.get(f"/api/v1/matches/?search={fragment}")
    assert response.status_code == 200
    results = items(response.json())
    assert any(m["id"] == live_seeded_match["id"] for m in results), (
        "Пошук іде по назвах команд (home__name, away__name), а не по id."
    )


def test_search_for_nonsense_returns_empty(api):
    response = api.get("/api/v1/matches/?search=zzzzzzzzzz")
    assert response.status_code == 200
    assert items(response.json()) == []


def test_ordering_descending(api):
    response = api.get("/api/v1/matches/?ordering=-starts_at")
    assert response.status_code == 200
    starts = [m["starts_at"] for m in items(response.json())]
    assert starts == sorted(starts, reverse=True), (
        "?ordering=-starts_at має віддати список від найпізнішого до найранішого."
    )


def test_default_ordering_is_ascending(api):
    response = api.get("/api/v1/matches/")
    assert response.status_code == 200
    starts = [m["starts_at"] for m in items(response.json())]
    assert starts == sorted(starts), (
        "Без ?ordering список іде за часом початку за зростанням."
    )


def test_scoreboard_order_survives_annotation(api, new_match):
    """Матч, що почався раніше за всіх, має стати першим на табло.

    Перевірка цілеспрямовано ловить одну помилку: у запиті з агрегацією
    Django **ігнорує** ``Meta.ordering``, тому анотований queryset іде без
    ``ORDER BY`` і порядок рядків стає випадковим. На трьох сидованих матчах
    він часто випадково правильний — тому тут створюється матч із датою
    раніше за сидовані.

    Звіряється **властивість порядку**, а не конкретний ``id``: якщо ви
    запускали набір кілька разів без ``seed_tournament --flush``, у базі вже
    лежать матчі з тією самою датою 2020 року з попередніх прогонів, і першим
    стане найстаріший із них. Для перевірки це байдуже.
    """
    early = new_match(starts_at="2020-01-01T12:00:00Z")
    response = api.patch(f"/api/v1/matches/{early['id']}/", json={"status": "live"})
    assert response.status_code == 200

    board = api.get("/api/v1/scoreboard/").json()
    starts = [match["starts_at"] for match in board]
    assert starts == sorted(starts), (
        "Табло впорядковане за часом початку. Якщо порядок зламався після "
        "переходу на annotate — додайте явний order_by() у queryset."
    )
    assert early["id"] in [match["id"] for match in board], (
        "Створений матч переведено в live, отже він має бути на табло."
    )
    assert board[0]["starts_at"] == early["starts_at"], (
        "Найраніший за часом початку матч має стояти першим. Якщо першим "
        "іде інший — порядок визначає база, а не ваш order_by()."
    )


def test_filter_and_ordering_work_together(api):
    response = api.get("/api/v1/matches/?status=scheduled&ordering=-starts_at")
    assert response.status_code == 200
    results = items(response.json())
    assert all(m["status"] == "scheduled" for m in results)
    starts = [m["starts_at"] for m in results]
    assert starts == sorted(starts, reverse=True)
