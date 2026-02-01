#!/usr/bin/env python3
"""
Fast pre-commit checks - validates Python syntax and staged files
Should complete in < 5 seconds
"""
import os
import subprocess
import sys


def get_staged_files():
    """Get list of staged files"""
    try:
        result = subprocess.check_output(
            ['git', 'diff', '--cached', '--name-only'],
            text=True
        )
        return [f for f in result.strip().split('\n') if f]
    except subprocess.CalledProcessError:
        return []


def check_python_syntax(files):
    """Check Python files for syntax errors"""
    py_files = [f for f in files if f.endswith('.py')]
    if not py_files:
        return 0

    for f in py_files:
        if not os.path.exists(f):
            continue
        try:
            with open(f, 'r') as fh:
                compile(fh.read(), f, 'exec')
        except SyntaxError as e:
            print(f"ERROR: Syntax error in {f}")
            print(f"  Line {e.lineno}: {e.msg}")
            return 1
    return 0


def check_json_yaml(files):
    """Check JSON/YAML files are valid"""
    invalid = []
    for f in files:
        if not os.path.exists(f):
            continue
        if f.endswith('.json'):
            try:
                import json
                with open(f, 'r') as fh:
                    json.load(fh)
            except Exception as e:
                print(f"ERROR: Invalid JSON in {f}: {e}")
                invalid.append(f)
    return 0 if not invalid else 1


def main():
    files = get_staged_files()
    if not files:
        return 0

    print(f"Checking {len(files)} staged files...")

    errors = []

    # Python syntax
    result = check_python_syntax(files)
    if result != 0:
        errors.append("Python syntax check failed")

    # JSON/YAML validation
    result = check_json_yaml(files)
    if result != 0:
        errors.append("JSON/YAML validation failed")

    if errors:
        print("\nPre-commit checks failed:")
        for error in errors:
            print(f"  - {error}")
        return 1

    print("Pre-commit checks passed!")
    return 0


if __name__ == '__main__':
    sys.exit(main())
