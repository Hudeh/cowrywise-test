# frontend_api/api/signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from decouple import config
from django.contrib.auth import get_user_model
import pika
import json
import os
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


@receiver(post_save, sender=User)
def publish_user_created(sender, instance, created, **kwargs):
    if created:
        message = {
            "action": "user_created",
            "user_data": {
                "id": instance.id,
                "first_name": instance.first_name,
                "last_name": instance.last_name,
                "email": instance.email
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
                    ),
                    heartbeat=600,
                    blocked_connection_timeout=300,
                )
            )
            channel = connection.channel()
            channel.queue_declare(queue="user_updates", durable=True)
            channel.basic_publish(
                exchange="",
                routing_key="user_updates",
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                ),
            )
            connection.close()
            logger.info(f"Published message to 'user_updates': {message}")
        except Exception as e:
            logger.error(f"Failed to publish message: {e}")
