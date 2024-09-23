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

urlpatterns = [
    path("", include(router.urls)),
    path("unavailable-books/", UnavailableBooksViewSet.as_view({"get": "list"})),
    path(
        "users-borrowed-books/",
        BorrowedBookViewSet.as_view({"get": "list_users_borrowed_books"}),
    ),
]
