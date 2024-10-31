#!/usr/bin/env python3
import pytest
import argparse
import sys
import os
from datetime import datetime
from pathlib import Path
import subprocess


def run_tests():
    args = sys.argv[1:]
    pytest_args = []

    # Handle test type filtering
    if '--type' in args:
        type_index = args.index('--type')
        if type_index + 1 < len(args):
            test_type = args[type_index + 1]
            if test_type == 'unit':
                pytest_args.extend(['-v', '-m', 'unit'])
            elif test_type == 'integration':
                pytest_args.extend(['-v', '-m', 'integration'])
            elif test_type == 'performance':
                pytest_args.extend(['-v', '-m', 'performance'])
            else:
                print(f"Unknown test type: {test_type}")
                sys.exit(1)

            # Remove the --type argument and its value
            args = args[:type_index] + args[type_index+2:]

    # Handle report generation
    if '--report' in args:
        report_index = args.index('--report')
        pytest_args.extend(['--html=report.html', '--self-contained-html'])
        args.pop(report_index)

    # Add any remaining arguments
    pytest_args.extend([arg for arg in args if arg not in pytest_args])

    # Run pytest with collected arguments
    sys.exit(pytest.main(pytest_args))


def setup_test_environment():
    """Setup test environment and verify configuration"""
    venv_path = Path('.venv-test')

    # Create venv if it doesn't exist
    if not venv_path.exists():
        print("Creating test virtual environment...")
        subprocess.run([sys.executable, '-m', 'venv',
                       str(venv_path)], check=True)

    # Determine pip path
    pip_path = venv_path / ('Scripts' if sys.platform ==
                            'win32' else 'bin') / 'pip'

    # Install dependencies
    print("Installing dependencies...")
    subprocess.run([str(pip_path), 'install', '-r',
                   'requirements.txt'], check=True)
    subprocess.run([str(pip_path), 'install', '-r',
                   'requirements-test.txt'], check=True)

    # Load test environment
    if not os.path.exists('.env.test'):
        print("ERROR: .env.test file not found!")
        print("Please create it with your test configuration")
        sys.exit(1)

    # Copy test env to active env
    subprocess.run(['cp', '.env.test', '.env'])

    return venv_path


if __name__ == '__main__':
    # Ensure required packages are installed
    try:
        import pytest_html
        import pytest_cov
    except ImportError:
        print("Installing required packages...")
        os.system('pip install pytest-html pytest-cov')

    # Setup test environment
    venv_path = setup_test_environment()

    # Run tests
    print(f"\nRunning tests...")
    exit_code = run_tests()

    # Print summary
    if '--report' in sys.argv:
        print("\nTest reports generated in test_reports/")

    sys.exit(exit_code)
