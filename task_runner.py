#!/usr/bin/env python
import os
import time
import subprocess
import django
from datetime import datetime

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'obscura.settings')
django.setup()

INTERVAL = 60


def main():
    print(f"Starting status updater at {datetime.now()}")

    while True:
        try:
            subprocess.run(['python', 'manage.py', 'update_user_status'], check=True)
            print(f"Status check completed at {datetime.now()}")
        except Exception as e:
            print(f"Error running status update: {e}")

        time.sleep(INTERVAL)


if __name__ == "__main__":
    main()