from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from decouple import config
from .models import User
from django.contrib.auth import get_user_model
import pika
import json


@receiver(post_save, sender=User)
def publish_user_created(sender, instance, created, **kwargs):
    if created:
        message = {
            "action": "user_created",
            "user_data": {
                "id": instance.id,
                "first_name": instance.first_name,
                "last_name": instance.last_name,
                "email": instance.email,
            },
        }
        try:
            # Establish connection
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

            # Ensure the queue exists
            channel.queue_declare(queue="library_queue", durable=True)

            # Publish the message
            channel.basic_publish(
                exchange="",
                routing_key="library_queue",
                body=json.dumps(message),
                properties=pika.BasicProperties(
                    delivery_mode=2,
                ),
            )

            connection.close()
            print(f"Published message to 'library_queue': {message}")
        except Exception as e:
            print(f"Failed to publish user creation message: {e}")
