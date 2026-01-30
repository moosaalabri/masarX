import socket
import sys
import os
from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connections
from django.db.utils import OperationalError

class Command(BaseCommand):
    help = 'Tests database connectivity step-by-step (DNS, TCP, Auth)'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS("=== Starting Database Connection Diagnostics ==="))
        
        # 1. Inspect Configuration
        db_conf = settings.DATABASES['default']
        host = db_conf.get('HOST')
        port = db_conf.get('PORT')
        user = db_conf.get('USER')
        name = db_conf.get('NAME')
        
        # Mask password
        password = db_conf.get('PASSWORD')
        masked_password = "*****" if password else "None"
        
        self.stdout.write(f"Configuration:")
        self.stdout.write(f"  HOST: {host}")
        self.stdout.write(f"  PORT: {port}")
        self.stdout.write(f"  USER: {user}")
        self.stdout.write(f"  NAME: {name}")
        self.stdout.write(f"  PASS: {masked_password}")
        
        if not host:
            self.stdout.write(self.style.ERROR("ERROR: DB_HOST is not set or empty."))
            return

        # 2. DNS Resolution
        self.stdout.write("\n--- Step 1: DNS Resolution ---")
        ip_address = None
        try:
            ip_address = socket.gethostbyname(host)
            self.stdout.write(self.style.SUCCESS(f"✔ Success: '{host}' resolved to {ip_address}"))
        except socket.gaierror as e:
            self.stdout.write(self.style.ERROR(f"✘ Failed: Could not resolve hostname '{host}'. Error: {e}"))
            self.stdout.write(self.style.WARNING("Tip: Check for typos in DB_HOST. If this is a Docker container, ensure it is in the same network."))
            return

        # 3. TCP Connection Test
        self.stdout.write("\n--- Step 2: TCP Connection Check ---")
        try:
            port_int = int(port)
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(5) # 5 second timeout
            result = sock.connect_ex((ip_address, port_int))
            if result == 0:
                self.stdout.write(self.style.SUCCESS(f"✔ Success: Connected to {ip_address}:{port_int} via TCP."))
            else:
                self.stdout.write(self.style.ERROR(f"✘ Failed: Could not connect to {ip_address}:{port_int}."))
                self.stdout.write(self.style.ERROR(f"  Error Code: {result} (Check OS specific socket error codes)"))
                self.stdout.write(self.style.WARNING("Possible causes:"))
                self.stdout.write("  1. Firewall blocking the port (Check 'Remote MySQL' in Hostinger/cPanel).")
                self.stdout.write("  2. Database server is down.")
                self.stdout.write("  3. Database is listening on localhost only (Bind Address issue).")
            sock.close()
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✘ Error during TCP check: {e}"))

        # 4. Django/Driver Connection Test
        self.stdout.write("\n--- Step 3: Database Authentication ---")
        try:
            conn = connections['default']
            conn.cursor() # Forces connection
            self.stdout.write(self.style.SUCCESS(f"✔ Success: Authenticated and connected to database '{name}'."))
        except OperationalError as e:
            self.stdout.write(self.style.ERROR("✘ Failed: Database Driver Error."))
            self.stdout.write(f"  Error: {e}")
            
            error_str = str(e)
            if "2003" in error_str:
                self.stdout.write(self.style.WARNING("\nAnalysis for Error 2003 (Can't connect to MySQL server):"))
                self.stdout.write("  - If TCP check (Step 2) failed: The issue is Network/Firewall.")
                self.stdout.write("  - If TCP check passed: The issue might be SSL/TLS requirements or packet filtering.")
            elif "1045" in error_str:
                self.stdout.write(self.style.WARNING("\nAnalysis for Error 1045 (Access Denied):"))
                self.stdout.write("  - User/Password is incorrect.")
                self.stdout.write("  - User is not allowed to connect from this specific IP (Hostinger 'Remote MySQL' whitelist).")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✘ Unexpected Error: {e}"))

        self.stdout.write("\n=== Diagnostics Complete ===")
