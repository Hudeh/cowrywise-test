from rest_framework import serializers
from .models import User, Book, BorrowedBook


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = "__all__"


class BookSerializer(serializers.ModelSerializer):
    class Meta:
        model = Book
        fields = "__all__"


class BorrowedBookSerializer(serializers.ModelSerializer):
    user = UserSerializer(read_only=True)
    book = BookSerializer(read_only=True)

    class Meta:
        model = BorrowedBook
        fields = ["id", "user", "book", "borrowed_date", "due_date"]

    def validate_due_date(self, value):
        if value < timezone.now().date():
            raise serializers.ValidationError("Due date cannot be in the past.")
        return value


class UnavailableBookSerializer(serializers.ModelSerializer):
    due_date = serializers.SerializerMethodField()

    class Meta:
        model = Book
        fields = ["id", "title", "due_date"]

    def get_due_date(self, obj):
        borrowed_book = obj.borrowed_books.first()
        if borrowed_book:
            return borrowed_book.due_date
        return None
