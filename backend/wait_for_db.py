import os
import time
import sys
import django
from django.db import connections
from django.db.utils import OperationalError

def wait_for_db():
    """Wait for database to become available"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'yoga_flashcards.settings')
    django.setup()
    
    db_conn = None
    max_attempts = 30
    attempt = 0
    
    while not db_conn and attempt < max_attempts:
        try:
            db_conn = connections['default']
            db_conn.ensure_connection()
            print("Database available!")
            break
        except OperationalError:
            attempt += 1
            print(f"Database unavailable, waiting 1 second... (attempt {attempt}/{max_attempts})")
            time.sleep(1)
    
    if not db_conn:
        print("Could not connect to database after 30 attempts")
        sys.exit(1)

if __name__ == '__main__':
    wait_for_db()
