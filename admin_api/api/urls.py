from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    UserViewSet,
    BookViewSet,
    BorrowedBookViewSet,
    UnavailableBooksViewSet,
)

router = DefaultRouter()
router.register(r"users", UserViewSet)
router.register(r"books", BookViewSet)
router.register(r"borrowed-books", BorrowedBookViewSet)
router.register(
    r"unavailable-books", UnavailableBooksViewSet, basename="unavailablebook"
)


urlpatterns = [
    path("", include(router.urls)),
]
