from django.db import models


class User(models.Model):
    email = models.EmailField(unique=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)

    def __str__(self):
        return self.email


class Book(models.Model):
    title = models.CharField(max_length=255)
    publisher = models.CharField(max_length=100)
    category = models.CharField(max_length=100)
    is_available = models.BooleanField(default=True)
    available_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return self.title


class BorrowedBook(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="borrowed_by")
    book = models.ForeignKey(
        Book, on_delete=models.CASCADE, related_name="borrowed_books"
    )
    borrowed_date = models.DateField(auto_now_add=True)
    due_date = models.DateField()

    class Meta:
        unique_together = ("book", "user", "due_date")

    def __str__(self):
        return f"{self.user.email} borrowed {self.book.title}"
