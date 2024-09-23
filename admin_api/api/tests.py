from django.test import TestCase
from .models import Book, User
from rest_framework.test import APIClient
from django.urls import reverse
import json


class BookTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.book_data = {
            "title": "Django for Beginners",
            "publisher": "Apress",
            "category": "Technology",
            "is_available": True,
        }
        self.book = Book.objects.create(**self.book_data)

    def test_add_book(self):
        response = self.client.post(
            reverse("book-list"),
            {
                "title": "New Book",
                "publisher": "Manning",
                "category": "Science",
                "is_available": True,
            },
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Book.objects.count(), 2)

    def test_remove_book(self):
        response = self.client.delete(reverse("book-detail", args=[self.book.id]))
        self.assertEqual(response.status_code, 204)
        self.assertEqual(Book.objects.count(), 0)


class UserTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user_data = {
            "email": "john.doe@example.com",
            "first_name": "John",
            "last_name": "Doe",
        }
        self.user = User.objects.create(**self.user_data)

    def test_add_user(self):
        response = self.client.post(
            reverse("user-list"),
            {"email": "jane.doe@example.com", "first_name": "Jane", "last_name": "Doe"},
            format="json",
        )
        self.assertEqual(response.status_code, 201)
        self.assertEqual(User.objects.count(), 2)
