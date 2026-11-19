from rest_framework import serializers

from .models import Event, Match, Tournament


class TournamentSerializer(serializers.HyperlinkedModelSerializer):
    matches_count = serializers.SerializerMethodField()

    def get_matches_count(self, obj):
        return obj.matches.count()

    class Meta:
        model = Tournament
        fields = ["id", "name", "slug", "starts_on", "matches_count"]  # noqa: RUF012


class EventSerializer(serializers.ModelSerializer):
    team_name = serializers.CharField(source="team.name", read_only=True)

    def validate_team(self, team):
        match = self.context["match"]
        if team.pk not in (match.home_id, match.away_id):
            raise serializers.ValidationError("Команда не грає в цьому матчі.")
        return team

    class Meta:
        model = Event
        fields = ["id", "kind", "minute", "player", "team", "team_name"]  # noqa: RUF012


class MatchSerializer(serializers.ModelSerializer):
    home_name = serializers.SerializerMethodField()
    away_name = serializers.SerializerMethodField()
    score = serializers.SerializerMethodField()

    def get_home_name(self, obj):
        return obj.home.name

    def get_away_name(self, obj):
        return obj.away.name

    def get_score(self, obj):
        goals = obj.events.filter(kind="goal")
        return {
            "home": goals.filter(team_id=obj.home_id).count(),
            "away": goals.filter(team_id=obj.away_id).count(),
        }

    def validate(self, attrs):
        home = attrs.get("home", getattr(self.instance, "home", None))
        away = attrs.get("away", getattr(self.instance, "away", None))
        if home is not None and home == away:
            raise serializers.ValidationError(
                {"away": "Господарі та гості мають бути різними командами."}
            )
        return attrs

    class Meta:
        model = Match
        fields = [  # noqa: RUF012
            "id",
            "tournament",
            "home",
            "away",
            "home_name",
            "away_name",
            "starts_at",
            "status",
            "score",
        ]


class MatchDetailSerializer(MatchSerializer):
    tournament_name = serializers.StringRelatedField(source="tournament.name")
    url = serializers.HyperlinkedIdentityField(view_name="match-detail")

    class Meta(MatchSerializer.Meta):
        fields = MatchSerializer.Meta.fields + ["tournament_name", "url"]
