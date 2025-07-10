import os
import sys
import subprocess
import time
import argparse
from pathlib import Path
from datetime import datetime
import json


class TestRunner:
    def __init__(self):
        self.project_root = Path.cwd()
        self.reports_dir = Path("tests/reports")
        self.reports_dir.mkdir(parents=True, exist_ok=True)
        self.start_time = None
        self.results = {}

    def clean_test_environment(self):
        print("Cleaning test environment...")

        test_db_files = [
            'test_db.sqlite3',
            'tests/test_db.sqlite3',
            'db.sqlite3',
            '.pytest_cache',
        ]

        for item in test_db_files:
            path = Path(item)
            if path.exists():
                try:
                    if path.is_dir():
                        import shutil
                        shutil.rmtree(path)
                        print(f"Removed directory {item}")
                    else:
                        path.unlink()
                        print(f"Removed file {item}")
                except Exception as e:
                    print(f"Could not remove {item}: {e}")

        test_dirs = [
            "tests/reports",
            "tests/reports/unit",
            "tests/reports/integration",
            "tests/reports/security",
            "tests/reports/performance",
            "tests/reports/frontend"
        ]

        for test_dir in test_dirs:
            Path(test_dir).mkdir(parents=True, exist_ok=True)

        print("✓ Test environment cleaned")

    def run_command(self, cmd, description, timeout=300, capture_output=True):
        print(f"\n{description}")
        print("=" * 60)
        print(f"Command: {cmd}")
        print(f"Timeout: {timeout} seconds")
        print("-" * 60)

        try:
            start_time = time.time()

            if capture_output:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    capture_output=True,
                    text=True,
                    timeout=timeout,
                    cwd=self.project_root
                )
            else:
                result = subprocess.run(
                    cmd,
                    shell=True,
                    timeout=timeout,
                    cwd=self.project_root
                )

            end_time = time.time()
            duration = end_time - start_time

            if capture_output:
                if result.stdout:
                    print(result.stdout)
                if result.stderr and result.returncode != 0:
                    print("STDERR:", result.stderr)

            success = result.returncode == 0

            status = "SUCCESS" if success else "FAILED"
            print(f"\n{status} - Duration: {duration:.1f}s")

            self.results[description] = {
                'success': success,
                'duration': duration,
                'return_code': result.returncode,
                'command': cmd
            }

            return success, duration, result

        except subprocess.TimeoutExpired:
            print(f"TIMEOUT after {timeout} seconds")
            self.results[description] = {
                'success': False,
                'duration': timeout,
                'return_code': -1,
                'error': 'Timeout',
                'command': cmd
            }
            return False, timeout, None

        except Exception as e:
            print(f"ERROR: {e}")
            self.results[description] = {
                'success': False,
                'duration': 0,
                'return_code': -1,
                'error': str(e),
                'command': cmd
            }
            return False, 0, None

    def run_setup_verification(self):
        return self.run_command(
            "python -m pytest tests/test_setup_verification.py -v",
            "Setup Verification Tests",
            timeout=120
        )

    def run_unit_tests(self, quick=False):
        if quick:
            cmd = "python -m pytest tests/unit/test_models.py -v --tb=short"
            timeout = 120
        else:
            cmd = "python -m pytest tests/unit/ -v --tb=short --cov=. --cov-report=html:tests/reports/unit/htmlcov"
            timeout = 300

        return self.run_command(
            cmd,
            "Unit Tests" + (" (Quick)" if quick else ""),
            timeout=timeout
        )

    def run_integration_tests(self, quick=False):
        if quick:
            cmd = "python -m pytest tests/integration/test_user_service_integration.py::TestAuthenticationFlow::test_complete_registration_flow -v --tb=short"
            timeout = 180
        else:
            cmd = "python -m pytest tests/integration/ -v --tb=short -m integration"
            timeout = 600

        return self.run_command(
            cmd,
            "Integration Tests" + (" (Quick)" if quick else ""),
            timeout=timeout
        )

    def run_security_tests(self, quick=False):
        if quick:
            cmd = "python -m pytest tests/security/test_security.py::TestSecuritySimple::test_authentication_required -v --tb=short"
            timeout = 120
        else:
            cmd = "python -m pytest tests/security/ -v --tb=short -m security"
            timeout = 300

        return self.run_command(
            cmd,
            "Security Tests" + (" (Quick)" if quick else ""),
            timeout=timeout
        )

    def run_performance_tests(self, quick=False):
        if quick:
            cmd = "python -m pytest tests/performance/test_performance_simple.py::TestBasicPerformance::test_homepage_load_performance -v --tb=short"
            timeout = 120
        else:
            cmd = "python -m pytest tests/performance/test_performance_simple.py -v --tb=short"
            timeout = 600

        return self.run_command(
            cmd,
            "Performance Tests" + (" (Quick)" if quick else ""),
            timeout=timeout
        )

    def run_frontend_tests(self, quick=False):
        if quick:
            cmd = "python -m pytest tests/frontend/test_frontend_simple.py::TestFrontendSimple::test_homepage_loads -v --tb=short"
            timeout = 120
        else:
            cmd = "python -m pytest tests/frontend/ -v --tb=short"
            timeout = 300

        return self.run_command(
            cmd,
            "Frontend Tests" + (" (Quick)" if quick else ""),
            timeout=timeout
        )

    def run_all_tests(self, quick=False):
        if quick:
            cmd = "python -m pytest tests/ -v --tb=short -x --maxfail=3"
            timeout = 600
        else:
            cmd = "python -m pytest tests/ -v --tb=short --cov=. --cov-report=html:tests/reports/htmlcov --html=tests/reports/full_test_report.html"
            timeout = 1800

        return self.run_command(
            cmd,
            "All Tests" + (" (Quick)" if quick else ""),
            timeout=timeout
        )

    def run_specific_tests(self, pattern):
        cmd = f"python -m pytest {pattern} -v --tb=short"
        return self.run_command(
            cmd,
            f"Specific Tests: {pattern}",
            timeout=300
        )

    def check_dependencies(self):
        print("🔍 Checking dependencies...")

        required_packages = [
            'pytest',
            'pytest-django',
            'django',
            'faker',
            'requests'
        ]

        missing = []
        for package in required_packages:
            try:
                __import__(package.replace('-', '_'))
                print(f"{package}")
            except ImportError:
                print(f"{package} - MISSING")
                missing.append(package)

        if missing:
            print(f"\nInstall missing packages:")
            print(f"pip install {' '.join(missing)}")
            return False

        print("All required dependencies found")
        return True

    def run_api_tests(self, quick=False):
        if quick:
            cmd = "python -m pytest tests/api/test_api.py::TestAPIComprehensive::test_search_users_api_various_queries -v --tb=short"
            timeout = 120
        else:
            cmd = "python -m pytest tests/api/ -v --tb=short"
            timeout = 300

        return self.run_command(
            cmd,
            "API Tests" + (" (Quick)" if quick else ""),
            timeout=timeout
        )

    def generate_report(self):
        report_file = self.reports_dir / f"test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        total_duration = sum(r.get('duration', 0) for r in self.results.values())
        successful_tests = sum(1 for r in self.results.values() if r.get('success', False))
        total_tests = len(self.results)

        report = {
            'timestamp': datetime.now().isoformat(),
            'summary': {
                'total_tests': total_tests,
                'successful_tests': successful_tests,
                'failed_tests': total_tests - successful_tests,
                'success_rate': (successful_tests / total_tests * 100) if total_tests > 0 else 0,
                'total_duration': total_duration
            },
            'results': self.results
        }

        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)

        print(f"\nTest Report Generated: {report_file}")
        return report

    def print_summary(self):
        if not self.results:
            print("No tests were run.")
            return

        print("\n" + "=" * 80)
        print("TEST SUMMARY")
        print("=" * 80)

        successful_tests = []
        failed_tests = []
        total_duration = 0

        for test_name, result in self.results.items():
            duration = result.get('duration', 0)
            total_duration += duration

            if result.get('success', False):
                successful_tests.append((test_name, duration))
                status = "✅"
            else:
                failed_tests.append((test_name, duration, result.get('error', 'Unknown error')))
                status = "❌"

            print(f"{status} {test_name:<40} {duration:>8.1f}s")

        print("-" * 80)
        print(f"SUCCESS: {len(successful_tests)}/{len(self.results)} tests passed")
        print(f"DURATION: {total_duration:.1f} seconds total")

        if failed_tests:
            print(f"\nFAILED TESTS:")
            for test_name, duration, error in failed_tests:
                print(f"   • {test_name} ({duration:.1f}s) - {error}")

        success_rate = len(successful_tests) / len(self.results) * 100
        print(f"\nSUCCESS RATE: {success_rate:.1f}%")

        if success_rate >= 90:
            print("Excellent! Your test suite is in great shape!")
        elif success_rate >= 70:
            print("Good! Most tests are passing.")
        elif success_rate >= 50:
            print("Some issues need attention.")
        else:
            print("Many tests are failing - needs investigation.")


def interactive_mode():
    runner = TestRunner()

    print("Obscura Messenger Comprehensive Test Runner")
    print("=" * 60)

    if not runner.check_dependencies():
        print("\nMissing dependencies. Please install them first.")
        return

    if not Path('manage.py').exists():
        print("Error: Please run this script from the project root directory (where manage.py is located)")
        return

    print(f"Project root: {runner.project_root}")

    test_options = {
        '1': {'name': 'Setup Verification', 'func': runner.run_setup_verification,
              'desc': 'Verify test environment is working'},
        '2': {'name': 'Unit Tests', 'func': lambda: runner.run_unit_tests(), 'desc': 'Test individual components'},
        '3': {'name': 'Integration Tests', 'func': lambda: runner.run_integration_tests(),
              'desc': 'Test component interactions'},
        '4': {'name': 'API Tests', 'func': lambda: runner.run_api_tests(), 'desc': 'Test API endpoints'},
        '5': {'name': 'Security Tests', 'func': lambda: runner.run_security_tests(), 'desc': 'Test security measures'},
        '6': {'name': 'Performance Tests', 'func': lambda: runner.run_performance_tests(),
              'desc': 'Test performance metrics'},
        '7': {'name': 'Frontend Tests', 'func': lambda: runner.run_frontend_tests(), 'desc': 'Test UI components'},
        '8': {'name': 'Quick Test Suite', 'func': lambda: run_quick_suite(runner),
              'desc': 'Run one test from each category'},
        '9': {'name': 'All Tests', 'func': lambda: runner.run_all_tests(), 'desc': 'Run complete test suite'},
        '10': {'name': 'Custom Pattern', 'func': lambda: run_custom_pattern(runner),
               'desc': 'Run tests matching pattern'},
    }

    while True:
        print("\nAvailable test suites:")
        for key, option in test_options.items():
            print(f"  {key:>2}. {option['name']:<20} - {option['desc']}")
        print("   c. Clean test environment")
        print("   r. Show last results")
        print("   q. Quit")

        choice = input("\nEnter your choice: ").strip()

        if choice.lower() == 'q':
            break
        elif choice.lower() == 'c':
            runner.clean_test_environment()
            continue
        elif choice.lower() == 'r':
            runner.print_summary()
            continue
        elif choice in test_options:
            option = test_options[choice]
            print(f"\nStarting: {option['name']}")

            clean = input("🧹 Clean test environment first? (y/n): ").strip().lower()
            if clean == 'y':
                runner.clean_test_environment()

            runner.start_time = time.time()
            option['func']()

            runner.print_summary()
            runner.generate_report()

        else:
            print("Invalid choice!")


def run_quick_suite(runner):
    quick_tests = [
        lambda: runner.run_setup_verification(),
        lambda: runner.run_unit_tests(quick=True),
        lambda: runner.run_integration_tests(quick=True),
        lambda: runner.run_api_tests(quick=True),
        lambda: runner.run_security_tests(quick=True),
        lambda: runner.run_performance_tests(quick=True),
        lambda: runner.run_frontend_tests(quick=True),
    ]

    print("Running Quick Test Suite...")
    for test_func in quick_tests:
        success, duration, result = test_func()
        if not success:
            print(f"Quick test failed, stopping suite.")
            break


def run_custom_pattern(runner):
    pattern = input("Enter test pattern (e.g., tests/unit/test_models.py::TestUserModel): ").strip()
    if pattern:
        runner.run_specific_tests(pattern)


def main():
    parser = argparse.ArgumentParser(description='Obscura Messenger Test Runner')
    parser.add_argument('--all', action='store_true', help='Run all tests')
    parser.add_argument('--quick', action='store_true', help='Run quick test suite')
    parser.add_argument('--unit', action='store_true', help='Run unit tests only')
    parser.add_argument('--integration', action='store_true', help='Run integration tests only')
    parser.add_argument('--api', action='store_true', help='Run API tests only')
    parser.add_argument('--security', action='store_true', help='Run security tests only')
    parser.add_argument('--performance', action='store_true', help='Run performance tests only')
    parser.add_argument('--frontend', action='store_true', help='Run frontend tests only')
    parser.add_argument('--clean', action='store_true', help='Clean test environment first')
    parser.add_argument('--pattern', type=str, help='Run tests matching pattern')
    parser.add_argument('--interactive', action='store_true', default=True, help='Run in interactive mode')

    args = parser.parse_args()

    if len(sys.argv) == 1:
        interactive_mode()
        return

    runner = TestRunner()

    if not runner.check_dependencies():
        sys.exit(1)

    if args.clean:
        runner.clean_test_environment()

    runner.start_time = time.time()

    if args.all:
        runner.run_all_tests()
    elif args.quick:
        run_quick_suite(runner)
    elif args.unit:
        runner.run_unit_tests()
    elif args.integration:
        runner.run_integration_tests()
    elif args.api:
        runner.run_api_tests()
    elif args.security:
        runner.run_security_tests()
    elif args.performance:
        runner.run_performance_tests()
    elif args.frontend:
        runner.run_frontend_tests()
    elif args.pattern:
        runner.run_specific_tests(args.pattern)
    else:
        interactive_mode()
        return

    runner.print_summary()
    runner.generate_report()


if __name__ == "__main__":
    main()