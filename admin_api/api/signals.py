from django.db.models.signals import post_save
from django.dispatch import receiver
from decouple import config
from .models import Book
import pika
import json
import os
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Book)
def publish_book_created(sender, instance, created, **kwargs):
    if created:
        message = {
            "action": "add",
            "book_data": {
                "id": instance.id,
                "title": instance.title,
                "publisher": instance.publisher,
                "category": instance.category,
                "is_available": instance.is_available,
            },
        }
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
            channel.basic_publish(
                exchange="",
                routing_key="library_queue",
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                ),
            )
            connection.close()
            logger.info(f"Published message to 'book_updates': {message}")
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
