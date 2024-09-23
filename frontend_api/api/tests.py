from django.test import TestCase
from .models import Book, BorrowedBook, User
from rest_framework.test import APIClient
from django.urls import reverse
from django.utils import timezone
from datetime import timedelta


class FrontendBookTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create(
            email="john.doe@example.com", first_name="John", last_name="Doe"
        )
        self.book = Book.objects.create(
            title="Django for Beginners",
            publisher="Apress",
            category="Technology",
            is_available=True,
        )

    def test_list_books(self):
        response = self.client.get(reverse("book-list"))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)

    def test_borrow_book(self):
        response = self.client.post(
            reverse("book-borrow", args=[self.book.id]),
            {"user_id": self.user.id, "days": 7},
            format="json",
        )
        self.assertEqual(response.status_code, 200)
        self.book.refresh_from_db()
        self.assertFalse(self.book.is_available)
        self.assertEqual(BorrowedBook.objects.count(), 1)

    def test_filter_books_by_publisher(self):
        response = self.client.get(reverse("book-list"), {"publisher": "Apress"})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 1)
