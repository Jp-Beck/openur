#!/usr/bin/env python3
"""
Development setup script for OpenUR.
"""
import os
import sys
import subprocess
import argparse

def run_command(cmd, description):
    """Run a command and handle errors."""
    print(f"Running: {description}")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✓ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def setup_development_environment():
    """Set up development environment."""
    print("Setting up OpenUR development environment...")

    # Install development dependencies
    dev_deps = [
        "pytest>=6.0.0",
        "pytest-cov>=2.0.0",
        "black>=21.0.0",
        "flake8>=3.8.0",
        "mypy>=0.800",
        "pre-commit>=2.0.0"
    ]

    for dep in dev_deps:
        if not run_command(f"pip install {dep}", f"Installing {dep}"):
            return False

    # Install package in development mode
    if not run_command("pip install -e .", "Installing OpenUR in development mode"):
        return False

    # Set up pre-commit hooks
    if not run_command("pre-commit install", "Setting up pre-commit hooks"):
        return False

    print("✓ Development environment setup complete!")
    return True

def run_tests():
    """Run the test suite."""
    print("Running tests...")
    return run_command("python -m pytest tests/ -v", "Running test suite")

def run_linting():
    """Run code linting."""
    print("Running code linting...")

    # Run flake8
    if not run_command("flake8 openur/ tests/", "Running flake8"):
        return False

    # Run black check
    if not run_command("black --check openur/ tests/", "Running black check"):
        return False

    # Run mypy
    if not run_command("mypy openur/", "Running mypy"):
        return False

    return True

def format_code():
    """Format code with black."""
    print("Formatting code...")
    return run_command("black openur/ tests/", "Formatting code with black")

def main():
    """Main function."""
    parser = argparse.ArgumentParser(description="OpenUR development tools")
    parser.add_argument("command", choices=["setup", "test", "lint", "format", "all"],
                       help="Command to run")

    args = parser.parse_args()

    if args.command == "setup":
        success = setup_development_environment()
    elif args.command == "test":
        success = run_tests()
    elif args.command == "lint":
        success = run_linting()
    elif args.command == "format":
        success = format_code()
    elif args.command == "all":
        success = (setup_development_environment() and
                  format_code() and
                  run_linting() and
                  run_tests())

    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
