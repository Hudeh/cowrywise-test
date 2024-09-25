import logging
import time
from django.db.models import Prefetch
from rest_framework import viewsets, status, mixins
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import User, Book, BorrowedBook
from decouple import config
from .serializers import (
    UserSerializer,
    BookSerializer,
    BorrowedBookSerializer,
    UnavailableBookSerializer,
)

logger = logging.getLogger(__name__)

class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class BookViewSet(viewsets.ModelViewSet):
    queryset = Book.objects.all()
    serializer_class = BookSerializer


class BorrowedBookViewSet(
    mixins.ListModelMixin, mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    queryset = BorrowedBook.objects.all()
    serializer_class = BorrowedBookSerializer

    @action(detail=False, methods=["get"], url_path="users-borrowed-books")
    def list_users_borrowed_books(self, request):
        users_with_borrowed_books = (
            User.objects.filter(borrowed_by__isnull=False)
            .distinct()
            .prefetch_related(
                Prefetch(
                    "borrowed_by",
                    queryset=BorrowedBook.objects.select_related("book"),
                )
            )
        )
        data = []
        for user in users_with_borrowed_books:
            borrowed_books = BookSerializer(
                [borrowed.book for borrowed in user.borrowed_by.all()], many=True
            ).data
            user_data = UserSerializer(user).data
            user_data["borrowed_books"] = borrowed_books
            data.append(user_data)

        return Response(data, status=status.HTTP_200_OK)


class UnavailableBooksViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Book.objects.filter(is_available=False)
    serializer_class = UnavailableBookSerializer
    http_method_names = ["get"]

    def list(self, request):
        serializer = self.get_serializer(self.queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
