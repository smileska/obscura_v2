#!/usr/bin/env python3
"""
Script to test the current setup after frontend/backend separation
Run this from your PROJECT ROOT directory (where you can see backend/ and frontend/ folders)
"""

import os
import subprocess
import sys
from pathlib import Path


def check_current_directory():
    """Check if we're in the correct directory"""
    current_dir = Path.cwd()
    backend_exists = Path('backend').exists()
    frontend_exists = Path('frontend').exists()

    print(f"📁 Current directory: {current_dir}")
    print(f"📁 Backend folder exists: {backend_exists}")
    print(f"📁 Frontend folder exists: {frontend_exists}")

    if not backend_exists or not frontend_exists:
        print("❌ Error: You must run this script from the project root directory!")
        print("   Navigate to where you can see both backend/ and frontend/ folders")
        print("   Use: cd ../../ to go up two levels from backend/obscura/")
        return False

    return True


def check_file_structure():
    """Check if the required files and directories exist"""
    print("\n🔍 Checking file structure...")

    required_paths = [
        'backend/obscura/settings.py',
        'backend/obscura/urls.py',
        'backend/manage.py',
        'staticfiles',
        'media',
    ]

    for path in required_paths:
        if Path(path).exists():
            print(f"✓ {path} exists")
        else:
            print(f"✗ {path} missing")

    # Check for frontend structure
    frontend_paths = [
        'frontend',
        'frontend/static',
        'frontend/templates',
    ]

    print("\n🔍 Checking frontend structure...")
    for path in frontend_paths:
        if Path(path).exists():
            print(f"✓ {path} exists")
        else:
            print(f"✗ {path} missing - needs to be created")


def check_templates():
    """Check if templates have been moved to frontend"""
    print("\n🔍 Checking templates...")

    backend_html = Path('backend/html')
    frontend_templates = Path('frontend/templates')

    if backend_html.exists():
        print(f"⚠ Found old templates in: {backend_html}")
        print("  Templates need to be moved to frontend/templates/")
        return False

    if frontend_templates.exists():
        template_files = list(frontend_templates.rglob('*.html'))
        print(f"✓ Frontend templates folder exists with {len(template_files)} HTML files")
        return True
    else:
        print("✗ Frontend templates folder doesn't exist")
        return False


def test_django_setup():
    """Test Django configuration"""
    print("\n🔧 Testing Django setup...")

    # Check if we can change to backend directory
    if not Path('backend').exists():
        print("✗ Backend directory not found")
        return False

    original_dir = os.getcwd()
    os.chdir('backend')

    try:
        # Test Django check
        print("Running Django check...")
        result = subprocess.run(['python', 'manage.py', 'check'],
                                capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            print("✓ Django check passed")
        else:
            print(f"✗ Django check failed:")
            print(f"  stdout: {result.stdout}")
            print(f"  stderr: {result.stderr}")

    except subprocess.TimeoutExpired:
        print("✗ Django check timed out")
    except Exception as e:
        print(f"✗ Error running Django check: {e}")

    finally:
        os.chdir(original_dir)


def run_development_server():
    """Start the development server for testing"""
    print("\n🚀 Starting development server...")
    print("Visit http://127.0.0.1:8000 to test your application")
    print("Press Ctrl+C to stop the server")

    if not Path('backend').exists():
        print("✗ Backend directory not found")
        return

    original_dir = os.getcwd()
    os.chdir('backend')

    try:
        subprocess.run(['python', 'manage.py', 'runserver'])
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
    except Exception as e:
        print(f"✗ Error starting server: {e}")
    finally:
        os.chdir(original_dir)


def create_missing_directories():
    """Create missing frontend directories"""
    print("\n📁 Creating missing directories...")

    directories = [
        'frontend',
        'frontend/templates',
        'frontend/static',
        'frontend/static/css',
        'frontend/static/js',
    ]

    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✓ Created/verified: {directory}")


if __name__ == '__main__':
    print("Testing Obscura Frontend/Backend Separation")
    print("=" * 50)

    # Check if we're in the right directory
    if not check_current_directory():
        sys.exit(1)

    # Create missing directories
    create_missing_directories()

    # Check file structure
    check_file_structure()

    # Check templates
    templates_ok = check_templates()

    if not templates_ok:
        print("\n⚠ Templates need to be moved from backend to frontend!")
        print("   Run the organize_directories.py script first")

    # Test Django
    test_django_setup()

    print("\n" + "=" * 50)
    print("SUMMARY:")
    print("=" * 50)

    if templates_ok:
        print("✓ Ready to test!")
        response = input("🚀 Start development server? (y/n): ")
        if response.lower() == 'y':
            run_development_server()
    else:
        print("⚠ Setup incomplete. Move templates first, then re-run this script.")