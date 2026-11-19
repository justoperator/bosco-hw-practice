"""Деталі матчу: вкладені події, url, назва турніру — і недоторканий список."""

from conftest import items

LIST_KEYS = {
    "id", "tournament", "home", "away", "home_name", "away_name",
    "starts_at", "status", "score",
}
DETAIL_KEYS = LIST_KEYS | {"url", "tournament_name", "events"}
EVENT_KEYS = {"id", "kind", "minute", "player", "team", "team_name"}


def test_list_item_shape_is_unchanged(api):
    """Головна перевірка дня: вкладені події **не** потрапили у список.

    Вкладеність у списку зламала б і контракт 2.16.3, і продуктивність —
    тому для деталей потрібен окремий серіалізатор, а не одне поле більше.
    """
    results = items(api.get("/api/v1/matches/").json())
    assert results
    for match in results:
        assert set(match) == LIST_KEYS, (
            "Набір полів у списку мусить лишитись рівно таким, як у ПР №2.16.3. "
            "Для деталей зробіть окремий серіалізатор і get_serializer_class()."
        )


def test_detail_has_nested_events_url_and_tournament_name(api, finished_match):
    response = api.get(f"/api/v1/matches/{finished_match['id']}/")
    assert response.status_code == 200
    body = response.json()
    assert set(body) == DETAIL_KEYS, (
        "У деталях з'являються три нові поля: url, tournament_name і events."
    )
    assert isinstance(body["events"], list)
    assert body["url"].startswith("http"), (
        "HyperlinkedIdentityField віддає абсолютну адресу, бо в контексті є request."
    )
    assert str(finished_match["id"]) in body["url"]
    assert isinstance(body["tournament_name"], str) and body["tournament_name"]


def test_nested_event_shape(api, finished_match):
    body = api.get(f"/api/v1/matches/{finished_match['id']}/").json()
    assert body["events"], "У сидованому завершеному матчі є події."
    for event in body["events"]:
        assert set(event) == EVENT_KEYS
        assert isinstance(event["team_name"], str)


def test_nested_events_agree_with_score(api, finished_match):
    """Два подання тих самих даних не мають суперечити одне одному."""
    body = api.get(f"/api/v1/matches/{finished_match['id']}/").json()
    goals = [e for e in body["events"] if e["kind"] == "goal"]
    home_goals = sum(1 for e in goals if e["team"] == body["home"])
    away_goals = sum(1 for e in goals if e["team"] == body["away"])
    assert (home_goals, away_goals) == (body["score"]["home"], body["score"]["away"]), (
        "Рахунок порахований анотацією має збігатися з вкладеними подіями. "
        "Розбіжність означає, що в annotate загубився фільтр kind='goal' "
        "або переплутано home і away."
    )


def test_nested_events_are_ordered_by_minute(api, finished_match):
    body = api.get(f"/api/v1/matches/{finished_match['id']}/").json()
    minutes = [e["minute"] for e in body["events"]]
    assert minutes == sorted(minutes)


def test_events_action_still_works(api, finished_match):
    """Регресія: @action із ПР №2.16.3 нікуди не зник і лишився голим масивом."""
    response = api.get(f"/api/v1/matches/{finished_match['id']}/events/")
    assert response.status_code == 200
    assert isinstance(response.json(), list)
