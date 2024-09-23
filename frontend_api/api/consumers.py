import pika
import json
import time
import logging
from django.conf import settings
from api.models import Book, User
from django.db import transaction
from decouple import config

logger = logging.getLogger(__name__)


def process_message(body):
    try:
        message = json.loads(body)
        action = message.get("action")

        if action == "add":
            book_data = message.get("book_data", {})
            with transaction.atomic():
                Book.objects.update_or_create(
                    id=book_data.get("id"),
                    defaults={
                        "title": book_data.get("title"),
                        "publisher": book_data.get("publisher"),
                        "category": book_data.get("category"),
                        "is_available": book_data.get("is_available"),
                    },
                )
            logger.info(f"Processed 'add' action for book ID: {book_data.get('id')}")

        elif action == "borrowed":
            book_id = message.get("book_id")
            user_id = message.get("user_id")
            try:
                user = User.objects.get(id=user_id)
                book = Book.objects.get(id=book_id)
                book.is_available = False
                book.user = user
                book.save()
                logger.info(f"Processed 'borrowed' action for book ID: {book_id}")
            except Book.DoesNotExist:
                logger.warning(f"Book with ID {book_id} does not exist.")
    except json.JSONDecodeError as e:
        logger.error(f"Invalid JSON message: {e}")
    except Exception as e:
        logger.error(f"Error processing message: {e}")


def callback(ch, method, properties, body):
    process_message(body)


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
            channel.queue_declare(queue="book_updates", durable=True)
            channel.basic_consume(
                queue="book_updates", on_message_callback=callback, auto_ack=True
            )
            logger.info("Started consuming from 'book_updates' queue.")
            channel.start_consuming()
        except pika.exceptions.AMQPConnectionError as e:
            logger.error(
                f"Connection to RabbitMQ failed: {e}. Retrying in 5 seconds..."
            )
            time.sleep(5)
        except Exception as e:
            logger.error(f"Unexpected error: {e}. Retrying in 5 seconds...")
            time.sleep(5)
