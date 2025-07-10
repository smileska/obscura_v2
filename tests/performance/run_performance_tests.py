#!/usr/bin/env python3
import os
import sys
import subprocess
import time
from pathlib import Path


def clean_test_database():
    test_db_files = [
        'test_db.sqlite3',
        'tests/test_db.sqlite3',
        'db.sqlite3'
    ]

    for db_file in test_db_files:
        if Path(db_file).exists():
            try:
                os.remove(db_file)
                print(f"✓ Removed {db_file}")
            except Exception as e:
                print(f"⚠ Could not remove {db_file}: {e}")


def run_command(cmd, description, timeout=300):
    print(f"\n {description}")
    print("=" * 50)

    try:
        start_time = time.time()
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        end_time = time.time()

        duration = end_time - start_time

        if result.stdout:
            print(result.stdout)

        if result.stderr and result.returncode != 0:
            print("STDERR:", result.stderr)

        success = result.returncode == 0
        print(f"\n{'SUCCESS' if success else 'FAILED'} - took {duration:.1f} seconds")

        return success

    except subprocess.TimeoutExpired:
        print(f"TIMEOUT after {timeout} seconds")
        return False
    except Exception as e:
        print(f"ERROR: {e}")
        return False


def main():
    print("Obscura Messenger Performance Test Runner")
    print("=" * 60)

    if not Path('manage.py').exists():
        print("Error: Please run this script from the project root directory (where manage.py is located)")
        sys.exit(1)

    print("Current directory:", Path.cwd())

    print("\nCleaning up old test data...")
    clean_test_database()

    tests = {
        '1': {
            'name': 'Simple Performance Tests (Recommended)',
            'cmd': 'python -m pytest tests/performance/test_performance_simple.py -v -s',
            'timeout': 180
        },
        '2': {
            'name': 'Basic Homepage Performance Test',
            'cmd': 'python -m pytest tests/performance/test_performance_simple.py::TestBasicPerformance::test_homepage_load_performance -v -s',
            'timeout': 60
        },
        '3': {
            'name': 'Fixed Comprehensive Performance Tests',
            'cmd': 'python -m pytest tests/performance/test_performance.py -v -s -m performance',
            'timeout': 600
        },
        '4': {
            'name': 'Database Performance Only',
            'cmd': 'python -m pytest tests/performance/test_performance.py::TestDatabasePerformance -v -s',
            'timeout': 300
        },
        '5': {
            'name': 'Memory Tests Only',
            'cmd': 'python -m pytest tests/performance/test_performance_simple.py::TestMemoryBasics -v -s',
            'timeout': 120
        },
        '6': {
            'name': 'All Performance Tests',
            'cmd': 'python -m pytest tests/performance/ -v -s',
            'timeout': 900
        }
    }

    print("\nAvailable performance tests:")
    for key, test in tests.items():
        print(f"  {key}. {test['name']}")
    print("  q. Quit")

    while True:
        choice = input("\nEnter your choice (1-6 or q): ").strip()

        if choice.lower() == 'q':
            print("Goodbye!")
            break

        if choice in tests:
            test = tests[choice]

            print(f"\nRunning: {test['name']}")
            print(f"Command: {test['cmd']}")
            print(f"Timeout: {test['timeout']} seconds")

            success = run_command(test['cmd'], test['name'], test['timeout'])

            if success:
                print(f"\n{test['name']} completed successfully!")
            else:
                print(f"\n{test['name']} failed.")
                print("\nTroubleshooting tips:")
                print("  • Try the simpler tests first (option 1 or 2)")
                print("  • Make sure all dependencies are installed: pip install -r requirements-testing.txt")
                print("  • Check if the database is locked by another process")
                print("  • Try running: python manage.py migrate")

            continue_choice = input("\nRun another test? (y/n): ").strip().lower()
            if continue_choice != 'y':
                break
        else:
            print("Invalid choice! Please enter 1-6 or q")

    print("\nPerformance Testing Summary:")
    print("=" * 40)


if __name__ == "__main__":
    main()