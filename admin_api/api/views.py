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

    def add_book(self, request):
        serializer = BookSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            self.notify_frontend('add', serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def remove_book(self, request, pk):
        book_data = self.get_object()
        book_data.delete()
        self.notify_frontend("remove", book_data)
        return Response(status=status.HTTP_204_NO_CONTENT)

    def notify_frontend(self, action, book_data):
        while True:
            try:
                connection = pika.BlockingConnection(
                    pika.ConnectionParameters(
                        host=config("RABBITMQ_HOST"),
                        credentials=pika.PlainCredentials(
                            config("RABBITMQ_DEFAULT_USER"),
                            config("RABBITMQ_DEFAULT_PASS"),
                        ),
                        heartbeat=600,
                        blocked_connection_timeout=300,
                    )
                )
                channel = connection.channel()
                channel.queue_declare(queue="book_updates")
                channel.basic_publish(
                    exchange="",
                    routing_key="book_updates",
                    body=json.dumps({"book_data": book_data, "action": action}),
                )
                connection.close()
            except pika.exceptions.AMQPConnectionError as e:
                logger.error(
                    f"Connection to RabbitMQ failed: {e}. Retrying in 5 seconds..."
                )
                time.sleep(5)
            except Exception as e:
                logger.error(f"Unexpected error: {e}. Retrying in 5 seconds...")
                time.sleep(5)


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
    queryset = Book.objects.filter(is_available=False).prefetch_related(
        Prefetch("borrowed_books", queryset=BorrowedBook.objects.select_related("user"))
    )
    serializer_class = UnavailableBookSerializer
    http_method_names = ["get"]

    def list(self, request):
        serializer = self.get_serializer(self.queryset, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)
