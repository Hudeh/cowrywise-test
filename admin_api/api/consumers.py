import pika
import json
import time
from decouple import config
from .models import Book, User, BorrowedBook
from django.db import transaction
from django.utils import timezone
from datetime import timedelta

def callback(ch, method, properties, body):
    data = json.loads(body)
    action = data.get("action")
    if action == "borrowed":
        book_id = data.get("book_id")
        user_id = data.get("user_id")
        days = data.get("days")
        handle_borrowed(book_id, user_id, days)
    elif action == "user_created":
        user_data = data.get("user_data")
        handle_user_created(user_data)


def handle_borrowed(book_id, user_id, days):
    try:
        user = User.objects.get(id=user_id)
        book = Book.objects.get(id=book_id)
        due_date = timezone.now().date() + timedelta(days=int(days))
        borrowed_book = BorrowedBook.objects.create(user=user, book=book, due_date=due_date)
        obj, _ = Book.objects.update_or_create(
            id=book_id, defaults={"is_available": False}
        )
        print(
            f"Book ID {book_id} marked as borrowed by User ID {user_id}. borrowed_book {borrowed_book.id} {due_date}"
        )
    except Book.DoesNotExist:
        print(f"Book with ID {book_id} does not exist.")


def handle_user_created(user_data):
    try:
        with transaction.atomic():
            user, created = User.objects.update_or_create(
                id=user_data.get("id"),
                defaults={
                    "first_name": user_data.get("first_name"),
                    "last_name": user_data.get("last_name"),
                    "email": user_data.get("email"),
                },
            )
            if created:
                print(f"New user created in admin_api: {user_data}")
            else:
                print(f"User updated in admin_api: {user_data}")
    except Exception as e:
        print(f"Failed to create or update user from message: {e}")


def start_consuming():
    while True:
        try:
            connection = pika.BlockingConnection(
                pika.ConnectionParameters(
                    host=config("RABBITMQ_HOST"),
                    virtual_host=config("RABBITMQ_VHOST"),
                    credentials=pika.PlainCredentials(
                        config("RABBITMQ_DEFAULT_USER"),
                        config("RABBITMQ_DEFAULT_PASS"),
                    )
                )
            )
            channel = connection.channel()
            channel.queue_declare(queue="library_queue", durable=True)
            channel.basic_consume(
                queue="library_queue", on_message_callback=callback, auto_ack=True
            )
            print("Started consuming from 'frontend_api' queue.")
            channel.start_consuming()
        except pika.exceptions.AMQPConnectionError as e:
            print(
                f"Connection to RabbitMQ failed: {e}. Retrying in 5 seconds..."
            )
            time.sleep(5)
        except Exception as e:
            print(f"Unexpected error: {e}. Retrying in 5 seconds...")
            time.sleep(5)
