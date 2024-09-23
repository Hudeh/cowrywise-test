from django.db.models import Prefetch
from rest_framework import viewsets, status, filters, mixins
from rest_framework.response import Response
from .models import Book, BorrowedBook, User
from .serializers import (
    BookSerializer,
    BorrowedBookSerializer,
    UserSerializer,
    UnavailableBookSerializer,
)
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.decorators import action
from django.utils import timezone
from datetime import timedelta
from decouple import config


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class BookViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Book.objects.filter(is_available=True)
    serializer_class = BookSerializer
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ["publisher", "category"]
    search_fields = ["title"]

    def notify_admin(self, book_id, user_id):
        """Send a notification to admin_api via RabbitMQ when a book is borrowed"""
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=config("RABBITMQ_HOST"),
                    virtual_host=config("RABBITMQ_VHOST"),
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

            # Create the message payload
            message = {
                "action": "borrowed",
                "book_id": book_id,
                "user_id": user_id,
            }

            # Send the message to the queue
            channel.basic_publish(
                exchange="",
                routing_key="book_updates",
                body=json.dumps(message),
            )
            connection.close()
        except Exception as e:
            print(f"Failed to send message to admin_api: {e}")

    @action(detail=True, methods=["post"])
    def borrow(self, request, pk=None):
        book = self.get_object()
        user_id = request.data.get("user_id")
        days = request.data.get("days", 14)

        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response(
                {"error": "User not found"}, status=status.HTTP_404_NOT_FOUND
            )

        if not book.is_available:
            return Response(
                {"error": "Book is not available"}, status=status.HTTP_400_BAD_REQUEST
            )

        due_date = timezone.now().date() + timedelta(days=int(days))
        borrowed_book = BorrowedBook.objects.create(
            user=user, book=book, due_date=due_date
        )
        book.is_available = False
        book.save()
        self.notify_admin(book.id, user.id)
        return Response(
            {"message": "Book borrowed successfully"}, status=status.HTTP_200_OK
        )


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
