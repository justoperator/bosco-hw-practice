"""Заміри кількості SQL-запитів — ПР №2.17.3.

Зовні, по HTTP, кількість запитів до бази не видна: відповідь однакова і для
трьох запитів, і для сорока трьох. Тому цей набір працює **всередині** Django.

    cp tests-django/test_queries.py scoreboard/
    python manage.py test scoreboard -v 2

Жодна перевірка не порівнює з абсолютним числом. Кожна заміряє той самий
запит **двічі** — на малій і на великій кількості рядків — і вимагає, щоб
число не змінилось. Підібрати таке число «щоб пройшло» неможливо.
"""

import datetime

from django.db import connection
from django.test import TestCase
from django.test.utils import CaptureQueriesContext
from django.utils import timezone

from scoreboard.models import Event, Match, Team, Tournament


class QueryCountTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        cls.tournament = Tournament.objects.create(
            name="Турнір для замірів", slug="zamiry", starts_on=datetime.date(2030, 1, 1)
        )
        cls.teams = [
            Team.objects.create(name=f"Команда {i}", short_name=f"K{i:02d}")
            for i in range(8)
        ]

    # -- допоміжне ---------------------------------------------------------

    def make_matches(self, count, goals_each=3, status=Match.Status.FINISHED):
        matches = []
        for i in range(count):
            home = self.teams[i % 4]
            away = self.teams[4 + i % 4]
            match = Match.objects.create(
                tournament=self.tournament,
                home=home,
                away=away,
                starts_at=timezone.now() + datetime.timedelta(days=i),
                status=status,
            )
            for goal in range(goals_each):
                Event.objects.create(
                    match=match,
                    team=home if goal % 2 == 0 else away,
                    kind=Event.Kind.GOAL,
                    minute=10 + goal,
                    player=f"Гравець {goal}",
                )
            matches.append(match)
        return matches

    def count_queries(self, url):
        with CaptureQueriesContext(connection) as captured:
            response = self.client.get(url)
            self.assertEqual(
                response.status_code, 200, response.content[:300]
            )
        return len(captured)

    # -- заміри ------------------------------------------------------------

    def test_match_list_does_not_grow_with_match_count(self):
        self.make_matches(3)
        few = self.count_queries("/api/v1/matches/?page_size=50")
        self.make_matches(12)
        many = self.count_queries("/api/v1/matches/?page_size=50")
        self.assertEqual(
            few,
            many,
            msg=(
                f"На 3 матчах — {few} запитів, на 15 — {many}. Кількість запитів "
                "не має залежати від кількості рядків. Якщо вона росте — рахунок "
                "усе ще обчислюється запитом на кожен матч; перенесіть його в "
                "annotate(Count(..., filter=...)), а назви команд — у "
                "select_related('home', 'away')."
            ),
        )

    def test_match_detail_does_not_grow_with_event_count(self):
        match = self.make_matches(1, goals_each=2)[0]
        few = self.count_queries(f"/api/v1/matches/{match.pk}/")
        more = self.make_matches(1, goals_each=20)[0]
        many = self.count_queries(f"/api/v1/matches/{more.pk}/")
        self.assertEqual(
            few,
            many,
            msg=(
                f"Матч із 2 подіями — {few} запитів, із 20 — {many}. Вкладені "
                "події повертають N+1 з іншого боку: потрібен "
                "prefetch_related('events') і select_related('team') на подіях."
            ),
        )

    def test_scoreboard_does_not_grow_with_match_count(self):
        self.make_matches(2, status=Match.Status.LIVE)
        few = self.count_queries("/api/v1/scoreboard/")
        self.make_matches(10, status=Match.Status.LIVE)
        many = self.count_queries("/api/v1/scoreboard/")
        self.assertEqual(
            few,
            many,
            msg=(
                f"Табло на 2 матчах — {few} запитів, на 12 — {many}. Табло "
                "використовує той самий queryset, що й список: якщо ви "
                "оптимізували лише ViewSet, @api_view лишився наївним."
            ),
        )

    def test_tournament_list_does_not_grow_with_tournament_count(self):
        self.make_matches(3)
        few = self.count_queries("/api/v1/tournaments/")
        for i in range(5):
            other = Tournament.objects.create(
                name=f"Турнір {i}", slug=f"turnir-{i}", starts_on=datetime.date(2031, 1, 1)
            )
            Match.objects.create(
                tournament=other,
                home=self.teams[0],
                away=self.teams[1],
                starts_at=timezone.now(),
            )
        many = self.count_queries("/api/v1/tournaments/")
        self.assertEqual(
            few,
            many,
            msg=(
                f"На 1 турнірі — {few} запитів, на 6 — {many}. matches_count у "
                "ПР №2.16.3 робив .count() на кожен турнір — це теж N+1, просто "
                "менш помітний."
            ),
        )
