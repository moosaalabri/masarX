import time
from django.db import connections
from django.db.utils import OperationalError
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    """Django command to pause execution until database is available"""
    
    # Critical: Disable system checks to prevent the command from crashing 
    # if the database is not yet available.
    requires_system_checks = []

    def handle(self, *args, **options):
        self.stdout.write('Waiting for database...')
        db_conn = None
        for i in range(30):  # Retry for 30 seconds
            try:
                db_conn = connections['default']
                # Try to actually connect
                db_conn.cursor()
                self.stdout.write(self.style.SUCCESS('Database available!'))
                return
            except OperationalError:
                self.stdout.write('Database unavailable, waiting 1 second...')
                time.sleep(1)
            except Exception as e:
                 self.stdout.write(self.style.WARNING(f'Database error: {e}, waiting 1 second...'))
                 time.sleep(1)
        
        self.stdout.write(self.style.ERROR('Database unavailable after 30 seconds.'))