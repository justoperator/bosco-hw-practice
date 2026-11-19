from django_filters.rest_framework.backends import DjangoFilterBackend
from rest_framework import status, viewsets
from rest_framework.decorators import action, api_view
from rest_framework.exceptions import APIException
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework.response import Response
from rest_framework.reverse import reverse

from .filters import MatchFilter
from .models import Match, Tournament
from .pagination import StandardResultsSetPagination
from .serializers import (
    EventSerializer,
    MatchDetailSerializer,
    MatchSerializer,
    TournamentSerializer,
)


class Conflict(APIException):
    status_code = status.HTTP_409_CONFLICT


class TournamentViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Tournament.objects.all()  # ty: ignore[missing-attribute]
    serializer_class = TournamentSerializer
    lookup_field = "slug"


class MatchViewSet(viewsets.ModelViewSet):
    queryset = Match.objects.all().order_by("starts_at", "id")  # ty: ignore[missing-attribute]
    serializer_class = MatchSerializer
    http_method_names = ["get", "post", "patch", "delete", "head", "options"]  # noqa: RUF012
    filter_backends = [DjangoFilterBackend, SearchFilter, OrderingFilter]  # noqa: RUF012
    filterset_class = MatchFilter
    search_fields = ["home__name", "away__name"]  # noqa: RUF012
    ordering_fields = ["starts_at"]  # noqa: RUF012
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        if self.action == "retrieve":
            return MatchDetailSerializer
        return MatchSerializer

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        data.pop("status", None)
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(status=Match.Status.SCHEDULED)
        location = reverse(
            "match-detail", args=[serializer.instance.pk], request=request
        )
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers={"Location": location},
        )

    def perform_update(self, serializer):
        current_status = serializer.instance.status
        new_status = serializer.validated_data.get("status", current_status)
        allowed_transitions = {
            (Match.Status.SCHEDULED, Match.Status.LIVE),
            (Match.Status.LIVE, Match.Status.FINISHED),
        }
        if (
            new_status != current_status
            and (current_status, new_status) not in allowed_transitions
        ):
            raise Conflict(
                {
                    "detail": f"Перехід {current_status} → {new_status} неможливий.",
                    "code": "invalid_status_transition",
                }
            )
        serializer.save()

    def perform_destroy(self, instance):
        if instance.status != Match.Status.SCHEDULED:
            raise Conflict(
                {
                    "detail": "Матч, що вже почався, видалити неможливо.",
                    "code": "match_started",
                }
            )
        instance.delete()

    @action(detail=True, methods=["get", "post"], url_path="events")
    def events(self, request, pk=None):
        match = self.get_object()
        context = {**self.get_serializer_context(), "match": match}
        if request.method == "GET":
            serializer = EventSerializer(match.events.all(), many=True, context=context)
            return Response(serializer.data)

        if match.status != Match.Status.LIVE:
            raise Conflict(
                {
                    "detail": "Події можна додавати лише до матчу, що триває.",
                    "code": "match_not_live",
                }
            )
        serializer = EventSerializer(data=request.data, context=context)
        serializer.is_valid(raise_exception=True)
        serializer.save(match=match)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view()
def scoreboard_view(request):
    matches = Match.objects.filter(status=Match.Status.LIVE).order_by(  # ty: ignore[missing-attribute]
        "starts_at", "-id"
    )
    serializer = MatchSerializer(matches, many=True, context={"request": request})
    return Response(serializer.data)
