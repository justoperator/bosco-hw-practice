from django.db.models.query_utils import Q
from django_filters import rest_framework as filters

from .models import Match


def filter_by_team(qs, name, value):
    return qs.filter(Q(home=value) | Q(away=value))


class MatchFilter(filters.FilterSet):
    status = filters.ChoiceFilter(choices=Match.Status.choices)
    tournament = filters.NumberFilter(field_name="tournament")
    team = filters.NumberFilter(field_name="team", method=filter_by_team)

    class Meta:
        model = Match
        fields = ["status", "tournament", "team"]  # noqa: RUF012
