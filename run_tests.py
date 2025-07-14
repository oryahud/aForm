#!/usr/bin/env python3
"""
Test runner script for aForm application
Provides convenient commands to run different test suites
"""

import sys
import subprocess
import argparse
from pathlib import Path

def run_command(command, description):
    """Run a command and handle output"""
    print(f"\n{'='*60}")
    print(f"Running: {description}")
    print(f"Command: {command}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(result.stdout)
        if result.stderr:
            print("STDERR:", result.stderr)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Command failed with exit code {e.returncode}")
        print("STDOUT:", e.stdout)
        print("STDERR:", e.stderr)
        return False

def main():
    parser = argparse.ArgumentParser(description='aForm Test Runner')
    parser.add_argument('--unit', action='store_true', help='Run only unit tests')
    parser.add_argument('--integration', action='store_true', help='Run only integration tests')
    parser.add_argument('--auth', action='store_true', help='Run only authentication tests')
    parser.add_argument('--database', action='store_true', help='Run only database tests')
    parser.add_argument('--forms', action='store_true', help='Run only form tests')
    parser.add_argument('--collaboration', action='store_true', help='Run only collaboration tests')
    parser.add_argument('--api', action='store_true', help='Run only API tests')
    parser.add_argument('--coverage', action='store_true', help='Run tests with coverage report')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--parallel', '-n', type=int, help='Number of parallel workers')
    parser.add_argument('--fast', action='store_true', help='Skip slow tests')
    parser.add_argument('--file', help='Run tests from specific file')
    parser.add_argument('--function', help='Run specific test function')
    
    args = parser.parse_args()
    
    # Build pytest command
    cmd_parts = ['pytest']
    
    # Add test directory
    cmd_parts.append('tests/')
    
    # Add specific test filters
    markers = []
    if args.unit:
        markers.append('unit')
    if args.integration:
        markers.append('integration')
    if args.auth:
        markers.append('auth')
    if args.database:
        markers.append('database')
    if args.forms:
        markers.append('forms')
    if args.collaboration:
        markers.append('collaboration')
    if args.api:
        markers.append('api')
    
    if markers:
        cmd_parts.extend(['-m', ' or '.join(markers)])
    
    # Add specific file or function
    if args.file:
        cmd_parts = ['pytest', args.file]
        if args.function:
            cmd_parts.append(f'::{args.function}')
    
    # Add coverage
    if args.coverage:
        cmd_parts.extend([
            '--cov=.',
            '--cov-report=html',
            '--cov-report=term-missing',
            '--cov-exclude=tests/*'
        ])
    
    # Add verbose output
    if args.verbose:
        cmd_parts.append('-v')
    else:
        cmd_parts.append('-q')
    
    # Add parallel execution
    if args.parallel:
        cmd_parts.extend(['-n', str(args.parallel)])
    
    # Skip slow tests
    if args.fast:
        cmd_parts.extend(['-m', 'not slow'])
    
    # Add color and other options
    cmd_parts.extend([
        '--color=yes',
        '--tb=short'
    ])
    
    command = ' '.join(cmd_parts)
    
    # Check if pytest is available
    try:
        result = subprocess.run(['python', '-m', 'pytest', '--version'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        try:
            result = subprocess.run(['pytest', '--version'], capture_output=True, check=True)
        except (subprocess.CalledProcessError, FileNotFoundError):
            print("❌ pytest not found. Please install test dependencies:")
            print("   pip install -r requirements.txt")
            return 1
    
    # Run the tests
    success = run_command(command, "Running aForm Tests")
    
    if args.coverage and success:
        print(f"\n📊 Coverage report generated in htmlcov/index.html")
    
    return 0 if success else 1

if __name__ == '__main__':
    sys.exit(main())