import pika
import json
import time
from models import Book, User
import logging
from django.db import transaction

logger = logging.getLogger(__name__)


def callback(ch, method, properties, body):
    data = json.loads(body)
    action = data.get("action")

    if action == "borrowed":
        book_id = data.get("book_id")
        user_id = data.get("user_id")
        handle_borrowed(book_id, user_id)
    elif action == "user_created":
        user_data = data.get("user_data")
        handle_user_created(user_data)


def handle_borrowed(book_id, user_id):
    try:
        user = User.objects.get(id=user_id)
        book = Book.objects.get(id=book_id)
        book.is_available = False
        book.user = user
        book.save()
        logger.info(f"Book ID {book_id} marked as borrowed by User ID {user_id}.")
    except Book.DoesNotExist:
        logger.warning(f"Book with ID {book_id} does not exist.")


def handle_user_created(user_data):
    try:
        with transaction.atomic():
            User.objects.create(
                id=user_data.get("id"),
                first_name=user_data.get("first_name"),
                last_name=user_data.get("last_name"),
                email=user_data.get("email"),
            )
        logger.info(f"User created: {user_data}")
    except Exception as e:
        logger.error(f"Failed to create user from message: {e}")


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
                    ),
                    heartbeat=600,
                    blocked_connection_timeout=300,
                )
            )
            channel = connection.channel()
            channel.queue_declare(queue="user_updates", durable=True)
            channel.basic_consume(
                queue="user_updates", on_message_callback=callback, auto_ack=True
            )
            logger.info("Started consuming from 'user_updates' queue.")
            channel.start_consuming()
        except pika.exceptions.AMQPConnectionError as e:
            logger.error(
                f"Connection to RabbitMQ failed: {e}. Retrying in 5 seconds..."
            )
            time.sleep(5)
        except Exception as e:
            logger.error(f"Unexpected error: {e}. Retrying in 5 seconds...")
            time.sleep(5)
