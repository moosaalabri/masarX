import time
import socket
from django.db import connections
from django.db.utils import OperationalError
from django.core.management.base import BaseCommand
from django.conf import settings

class Command(BaseCommand):
    """Django command to pause execution until database is available"""
    requires_system_checks = []

    def handle(self, *args, **options):
        db_conf = settings.DATABASES['default']
        host = db_conf.get('HOST')
        port = db_conf.get('PORT')
        
        self.stdout.write(f"Debug Info - Host: {host}, Port: {port}, User: {db_conf.get('USER')}")

        # Try to resolve host immediately to catch DNS issues
        try:
            ip = socket.gethostbyname(host)
            self.stdout.write(f"DEBUG: Host '{host}' resolves to IP: {ip}")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"DEBUG ERROR: Could not resolve hostname '{host}': {e}"))

        self.stdout.write('Waiting for database...')
        for i in range(30):
            try:
                connections['default'].cursor()
                self.stdout.write(self.style.SUCCESS('Database available!'))
                return
            except OperationalError as e:
                error_str = str(e)
                if "2003" in error_str:
                    self.stdout.write(self.style.WARNING(f"Connection Failed (Attempt {i+1}/30): Error 2003 - Can't connect to MySQL server."))
                    # Perform a quick TCP check
                    try:
                        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                        sock.settimeout(2)
                        result = sock.connect_ex((host, int(port)))
                        if result == 0:
                            self.stdout.write(f"  > TCP Check: SUCCESS. Server is reachable at {host}:{port}. Issue is likely Auth/SSL or strict User Host limits.")
                        else:
                            self.stdout.write(f"  > TCP Check: FAILED (Code {result}). Server is NOT reachable at {host}:{port}. Check Firewall/IP.")
                        sock.close()
                    except Exception as tcp_e:
                        self.stdout.write(f"  > TCP Check Error: {tcp_e}")
                
                elif "1049" in error_str: # Unknown database
                     self.stdout.write(self.style.ERROR(f"CRITICAL: Database '{db_conf.get('NAME')}' does not exist."))
                     return
                else:
                    self.stdout.write(f'Database unavailable (Error: {e}), waiting 1 second...')
                
                time.sleep(1)
            except Exception as e:
                 self.stdout.write(self.style.WARNING(f'Database error: {e}, waiting 1 second...'))
                 time.sleep(1)
        
        self.stdout.write(self.style.ERROR('Database unavailable after 30 seconds.'))