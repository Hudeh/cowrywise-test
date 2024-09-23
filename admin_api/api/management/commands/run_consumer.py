from django.core.management.base import BaseCommand
from api.consumers import start_consuming


class Command(BaseCommand):
    help = "Starts the RabbitMQ consumer to listen"

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("Starting RabbitMQ consumer admin_api..."))
        start_consuming()
