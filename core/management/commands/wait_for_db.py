import time
from django.db import connections
from django.db.utils import OperationalError
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    """Django command to pause execution until database is available"""
    
    # Critical: Disable system checks to prevent the command from crashing 
    # if the database is not yet available.
    requires_system_checks = []

    def handle(self, *args, **options):
        # Print the connection details (masked password) for debugging
        db_conf = settings.DATABASES['default']
        self.stdout.write(f"Debug Info - Host: {db_conf.get('HOST')}, Port: {db_conf.get('PORT')}, Name: {db_conf.get('NAME')}, User: {db_conf.get('USER')}")

        # DEBUG: Check which MySQLdb is loaded
        try:
            import MySQLdb
            self.stdout.write(f"DEBUG: MySQLdb module is: {MySQLdb}")
            if hasattr(MySQLdb, '__file__'):
                 self.stdout.write(f"DEBUG: MySQLdb location: {MySQLdb.__file__}")
        except ImportError:
            self.stdout.write("DEBUG: MySQLdb module could NOT be imported.")

        self.stdout.write('Waiting for database...')
        db_conn = None
        for i in range(30):  # Retry for 30 seconds
            try:
                db_conn = connections['default']
                # Try to actually connect
                db_conn.cursor()
                self.stdout.write(self.style.SUCCESS('Database available!'))
                return
            except OperationalError as e:
                # Check for specific "Unknown database" error (MySQL code 1049)
                error_str = str(e)
                if "1049" in error_str or "Unknown database" in error_str:
                     self.stdout.write(self.style.ERROR(f"CRITICAL ERROR: The database '{db_conf.get('NAME')}' does not exist on the server."))
                     self.stdout.write(self.style.ERROR("Solution: Check your DB_NAME environment variable. It usually defaults to 'default' or the service name."))
                     # Fail immediately for this specific error as it won't resolve itself
                     return

                # Print the full error message
                self.stdout.write(f'Database unavailable (Error: {e}), waiting 1 second...')
                time.sleep(1)
            except Exception as e:
                 self.stdout.write(self.style.WARNING(f'Database error: {e}, waiting 1 second...'))
                 time.sleep(1)
        
        self.stdout.write(self.style.ERROR('Database unavailable after 30 seconds.'))