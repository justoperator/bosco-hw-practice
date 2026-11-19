# Тести ПР №2.17.3

Контракт — `../openapi.yaml` (версія 2.0.0). Тести перевіряють саме його;
при розбіжності правильний контракт, а не тест.

Два незалежні набори. Перший — black-box по HTTP, як у ПР №2.16.3: нічого не
знає про ваш проєкт, перевіряє лише контракт. Другий — всередині Django, бо
кількість SQL-запитів зовні не видно.

## 1. Контракт (black-box, pytest)

```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt

# в іншому терміналі:
#   python manage.py seed_tournament
#   python manage.py runserver

pytest                                    # http://127.0.0.1:8000
pytest --base-url http://localhost:8001
pytest test_cors.py -q                    # одна група
```

Рекомендований порядок роботи:

1. `pytest test_filters.py` — DjangoFilterBackend, SearchFilter, OrderingFilter
2. `pytest test_pagination.py` — `page_size_query_param` і `max_page_size`
3. `pytest test_detail.py` — окремий серіалізатор деталей, вкладені події, `url`
4. `pytest test_negotiation.py` — CSV-рендерер, `406`, `415`, `X-Poll-After`
5. `pytest test_cors.py` — django-cors-headers і порядок middleware
6. `pytest` — усе разом

**Прогін контрактних тестів ПР №2.16.3 має лишитись зеленим.** Це частина
завдання: розширення не ламає того, що вже обіцяно клієнтам. Запустіть старий
набір окремо — усі 38 перевірок мусять пройти на тому самому коді.

## 2. Кількість запитів (всередині Django)

`test_queries.py` з теки `tests-django/` скопіюйте в застосунок:

```bash
cp tests-django/test_queries.py scoreboard/
python manage.py test scoreboard -v 2
```

Цей набір не перевіряє абсолютних чисел — він **двічі** заміряє той самий
запит на різній кількості матчів і порівнює. Так тест не ламається від зміни
версії DRF і не дає підібрати число «щоб пройшло»: або кількість запитів не
залежить від кількості рядків, або залежить.

## Чому тести не перевіряють абсолютних кількостей матчів

Контракт забороняє видаляти матч, що почався, тому тести не можуть прибрати
за собою все, що створили. Жодна перевірка не спирається на загальну
кількість — лише на сидований турнір і на власні створені об'єкти. Для
чистого стану: `python manage.py seed_tournament --flush`.
