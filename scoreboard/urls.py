from django.urls import include, path
from rest_framework import routers

from .views import MatchViewSet, TournamentViewSet, scoreboard_view

router = routers.DefaultRouter()
router.register(r"tournaments", TournamentViewSet)
router.register(r"matches", MatchViewSet)

urlpatterns = [
    path("", include(router.urls)),
    path("scoreboard/", scoreboard_view),
]
