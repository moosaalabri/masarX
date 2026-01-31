from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
import os

class Command(BaseCommand):
    help = 'Ensures an admin user exists (idempotent)'

    def handle(self, *args, **options):
        User = get_user_model()
        username = os.environ.get('ADMIN_USER', 'admin')
        email = os.environ.get('ADMIN_EMAIL', 'admin@example.com')
        password = os.environ.get('ADMIN_PASS', 'admin')

        if not User.objects.filter(username=username).exists():
            self.stdout.write(f"Creating superuser '{username}'...")
            User.objects.create_superuser(username, email, password)
            self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' created successfully."))
        else:
            self.stdout.write(self.style.SUCCESS(f"Superuser '{username}' already exists. Skipping creation."))
